#!/usr/bin/env python3

from nipype.interfaces.fsl import Reorient2Std
from nipype.interfaces import afni
from PUMI.engine import BidsPipeline, NestedNode as Node, FuncPipeline, GroupPipeline, BidsApp, \
    create_dataset_description
from PUMI.pipelines.anat.anat_proc import anat_proc
from PUMI.pipelines.func.compcor import anat_noise_roi, compcor
from PUMI.pipelines.anat.func_to_anat import func2anat
from nipype.interfaces import utility
from PUMI.pipelines.func.func_proc import func_proc_despike_afni
from PUMI.pipelines.func.timeseries_extractor import pick_atlas, extract_timeseries_nativespace
from PUMI.utils import mist_modules, mist_labels, get_reference
from PUMI.pipelines.func.func2standard import func2standard
from PUMI.pipelines.multimodal.image_manipulation import pick_volume
import traits
import os


def relabel_mist_atlas(atlas_file, modules, labels):
    """
       Relabel MIST atlas
       * Beware : currently works only with labelmap!!
       Parameters:
           atlas_file(str): Path to the atlas file
           modules ([str]): List containing the modules in MIST
           labels ([str]): List containing the labels in MIST
       Returns:
           relabel_file (str): Path to relabeld atlas file
           reordered_modules ([str]): list containing reordered module names
           reordered_labels ([str]): list containing reordered label names
           new_labels (str): Path to .tsv-file with the new labels
    """

    import os
    import numpy as np
    import pandas as pd
    import nibabel as nib

    df = pd.DataFrame({'modules': modules, 'labels': labels})
    df.index += 1  # indexing from 1

    reordered = df.sort_values(by='modules')

    # relabel labelmap
    img = nib.load(atlas_file)
    if len(img.shape) != 3:
        raise Exception("relabeling does not work for probability maps!")

    lut = reordered.reset_index().sort_values(by="index").index.values + 1
    lut = np.array([0] + lut.tolist())
    # maybe this is a bit complicated, but believe me it does what it should

    data = img.get_fdata()
    newdata = lut[np.array(data, dtype=np.int32)]  # apply lookup table to swap labels

    img = nib.Nifti1Image(newdata.astype(np.float64), img.affine)
    nib.save(img, 'relabeled_atlas.nii.gz')

    out = reordered.reset_index()
    out.index = out.index + 1
    relabel_file = os.path.join(os.getcwd(), 'relabeled_atlas.nii.gz')
    reordered_modules = reordered['modules'].values.tolist()
    reordered_labels = reordered['labels'].values.tolist()

    newlabels_file = os.path.join(os.getcwd(), 'newlabels.tsv')
    out.to_csv(newlabels_file, sep='\t')
    return relabel_file, reordered_modules, reordered_labels, newlabels_file

@GroupPipeline(inputspec_fields=['labelmap', 'modules', 'labels'],
              outputspec_fields=['relabeled_atlas', 'reordered_labels', 'reordered_modules'])
def mist_atlas(wf, reorder=True, **kwargs):

    resample_atlas = Node(
        interface=afni.Resample(
            outputtype='NIFTI_GZ',
            master=get_reference(wf, 'brain'),
        ),
        name='resample_atlas'
    )

    if reorder:
        # reorder if modules is given (like for MIST atlases)
        relabel_atls = Node(
            interface=utility.Function(
                input_names=['atlas_file', 'modules', 'labels'],
                output_names=['relabelled_atlas_file', 'reordered_modules', 'reordered_labels', 'newlabels_file'],
                function=relabel_mist_atlas
            ),
            name='relabel_atls'
        )
        wf.connect('inputspec', 'labelmap', relabel_atls, 'atlas_file')
        wf.connect('inputspec', 'modules', relabel_atls, 'modules')
        wf.connect('inputspec', 'labels', relabel_atls, 'labels')

        wf.connect(relabel_atls, 'relabelled_atlas_file', resample_atlas, 'in_file')
    else:
        wf.connect('inputspec', 'labelmap', resample_atlas, 'in_file')

    # Sinking
    wf.connect(resample_atlas, 'out_file', 'sinker', 'atlas')
    if reorder:
        wf.connect(relabel_atls, 'newlabels_file', 'sinker', 'reordered_labels')
    else:
        wf.connect('inputspec', 'labels', 'sinker', 'atlas_labels')

    # Output
    wf.connect(resample_atlas, 'out_file', 'outputspec', 'relabeled_atlas')
    if reorder:
        wf.connect(relabel_atls, 'reordered_labels', 'outputspec', 'reordered_labels')
        wf.connect(relabel_atls, 'reordered_modules', 'outputspec', 'reordered_modules')
    else:
        wf.connect('inputspec', 'labels', 'outputspec', 'reordered_labels')
        wf.connect('inputspec', 'modules', 'outputspec', 'reordered_modules')


@FuncPipeline(inputspec_fields=['ts_files', 'fd_files', 'scrub_threshold'],
              outputspec_fields=['features', 'out_file'])
def calculate_connectivity(wf, **kwargs):

    def calc_connectivity(ts_files, fd_files, scrub_threshold):
        import os
        import pandas as pd
        import numpy as np
        from PUMI.PAINTeR import load_timeseries, connectivity_matrix

        if not isinstance(ts_files, (list, np.ndarray)):  # in this case we assume we have a string or path-like object
            ts_files = [ts_files]
        if not isinstance(fd_files, (list, np.ndarray)):  # in this case we assume we have a string or path-like object
            fd_files = [fd_files]
        FD = []
        mean_FD = []
        median_FD = []
        max_FD = []
        perc_scrubbed = []
        for f in fd_files:
            fd = pd.read_csv(f, sep="\t").values.flatten()
            fd = np.insert(fd, 0, 0)
            FD.append(fd.ravel())
            mean_FD.append(fd.mean())
            median_FD.append(np.median(fd))
            max_FD.append(fd.max())
            perc_scrubbed.append(100 - 100 * len(fd) / len(fd[fd <= scrub_threshold]))

        df = pd.DataFrame()
        df['ts_file'] = ts_files
        df['fd_file'] = fd_files
        df['meanFD'] = mean_FD
        df['medianFD'] = median_FD
        df['maxFD'] = max_FD
        df['perc_scrubbed'] = perc_scrubbed

        ts, labels = load_timeseries(ts_files, df, scrubbing=True, scrub_threshold=scrub_threshold)
        features, cm = connectivity_matrix(np.array(ts))

        path = os.path.abspath('motion.csv')
        df.to_csv(path)
        return features, path

    connectivity_wf = Node(
        utility.Function(
            input_names=['ts_files', 'fd_files', 'scrub_threshold'],
            output_names=['features', 'out_file'],
            function=calc_connectivity
        ),
        name="connectivity_wf"
    )
    wf.connect('inputspec', 'ts_files', connectivity_wf, 'ts_files')
    wf.connect('inputspec', 'fd_files', connectivity_wf, 'fd_files')

    if isinstance(wf.get_node('inputspec').inputs.scrub_threshold, traits.trait_base._Undefined):
        connectivity_wf.inputs.scrub_threshold = .15
    else:
        wf.connect('inputspec', 'scrub_threshold', connectivity_wf, 'scrub_threshold')

    wf.connect(connectivity_wf, 'features', 'outputspec', 'features')
    wf.connect(connectivity_wf, 'out_file', 'outputspec', 'out_file')

    wf.connect(connectivity_wf, 'out_file', 'sinker', 'connectivity')


@FuncPipeline(inputspec_fields=['X', 'in_file'],
              outputspec_fields=['score', 'out_file'])
def predict_pain_sensitivity_rpn(wf, **kwargs):
    """

    Perform pain sensitivity prediction using the RPN signature
    (Resting-state Pain susceptibility Network signature).
    Further information regarding the signature: https://spisakt.github.io/RPN-signature/

    Inputs:
        X (array-like): Input data for pain sensitivity prediction
        in_file (str): Path to the bold file that was used to create X

    Outputs:
        predicted (float): Predicted pain sensitivity score
        out_file (str): Absolute path to the output CSV file containing the prediction result

    Sinking:
        CSV file containing the prediction result

    """

    def predict(X, in_file):
        from PUMI.utils import rpn_model
        import pandas as pd
        import PUMI
        import os
        import importlib

        with importlib.resources.path('resources', 'model_rpn.json') as file:
            model_json = file

        model = rpn_model(file=model_json)
        predicted = model.predict(X)

        path = os.path.abspath('rpn-prediction.csv')
        df = pd.DataFrame()
        df['in_file'] = [in_file]
        df['RPN'] = predicted
        df.to_csv(path, index=False)
        return predicted, path

    predict_wf = Node(
        utility.Function(
            input_names=['X', 'in_file'],
            output_names=['score', 'out_file'],
            function=predict
        ),
        name="predict_wf"
    )
    wf.connect('inputspec', 'X', predict_wf, 'X')
    wf.connect('inputspec', 'in_file', predict_wf, 'in_file')

    wf.connect(predict_wf, 'score', 'outputspec', 'score')
    wf.connect(predict_wf, 'out_file', 'outputspec', 'out_file')
    wf.connect(predict_wf, 'out_file', 'sinker', 'rpn')


@FuncPipeline(inputspec_fields=['X', 'in_file'],
              outputspec_fields=['score', 'out_file'])
def predict_pain_sensitivity_rcpl(wf, model_path=None, **kwargs):
    """

    Perform pain sensitivity prediction using RCPL signature
    (Resting-state functional Connectivity signature of Pain-related Learning).
    Further information regarding the signature: https://github.com/kincsesbalint/paintone_rsn

    Parameters:
        model_path (str, optional): Path to the pre-trained model relative to PUMI's data_in folder.
                                    If set to None, PUMI's build in RCPL model is used.

    Inputs:
        X (array-like): Input data for pain sensitivity prediction
        in_file (str): Path to the bold file that was used to create X

    Outputs:
        predicted (float): Predicted pain sensitivity score
        out_file (str): Absolute path to the output CSV file containing the prediction result

    Sinking:
        CSV file containing the prediction result

    """

    def predict(X, in_file, model_path):
        import pandas as pd
        import os
        import PUMI
        import joblib
        import importlib

        if model_path is None:
            with importlib.resources.path('resources', 'rcpl_model.sav') as file:
                model = joblib.load(file)
        else:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")

            data_in_folder = os.path.join(os.path.dirname(os.path.abspath(PUMI.__file__)), '..', 'data_in')
            model_path = os.path.join(data_in_folder, model_path)
            model = joblib.load(model_path)

        predicted = model.predict(X)

        path = os.path.abspath('rcpl-prediction.csv')
        df = pd.DataFrame()
        df['in_file'] = [in_file]
        df['RCPL'] = predicted
        df.to_csv(path, index=False)

        return predicted, path

    predict_wf = Node(
        utility.Function(
            input_names=['X', 'in_file', 'model_path'],
            output_names=['score', 'out_file'],
            function=predict
        ),
        name="predict_wf"
    )
    wf.connect('inputspec', 'X', predict_wf, 'X')
    wf.connect('inputspec', 'in_file', predict_wf, 'in_file')
    predict_wf.inputs.model_path = model_path

    wf.connect(predict_wf, 'score', 'outputspec', 'score')
    wf.connect(predict_wf, 'out_file', 'outputspec', 'out_file')
    wf.connect(predict_wf, 'out_file', 'sinker', 'rcpl')


@FuncPipeline(inputspec_fields=['rpn_out_file', 'rcpl_out_file'],
              outputspec_fields=['out_file'])
def collect_pain_predictions(wf, **kwargs):
    """

    Merge the out_file's of pain sensitivity predictions generated using the RCPL and RPN methods into one file

    Inputs:
        rpn_out_file (str): Path to the out_file generated by the RPN method
        rcpl_out_file (str): Path to the out_file generated by the RCPL method

    Outputs:
        out_file (str): Absolute path to the output CSV file containing the RPN and RCPL predictions.

    Sinking:
        CSV file containing RPN and RCPL predictions

   """

    def merge_predictions(rpn_out_file, rcpl_out_file):
        import pandas as pd
        import os

        df_rpn = pd.read_csv(rpn_out_file)
        df_rcpl = pd.read_csv(rcpl_out_file)

        # Check if in_file columns are the same
        if df_rpn['in_file'].iloc[0] != df_rcpl['in_file'].iloc[0]:
            raise ValueError("The 'in_file' columns in the two CSV files are not the same!")

        merged_df = pd.DataFrame()
        merged_df['in_file'] = df_rpn['in_file']
        merged_df['RPN'] = df_rpn['RPN']
        merged_df['RCPL'] = df_rcpl['RCPL']

        path = os.path.abspath('pain-sensitivity-predictions.csv')
        merged_df.to_csv(path, index=False)

        return path

    merge_predictions_wf = Node(
        utility.Function(
            input_names=['rpn_out_file', 'rcpl_out_file'],
            output_names=['out_file'],
            function=merge_predictions
        ),
        name="merge_predictions_wf"
    )
    wf.connect('inputspec', 'rpn_out_file', merge_predictions_wf, 'rpn_out_file')
    wf.connect('inputspec', 'rcpl_out_file', merge_predictions_wf, 'rcpl_out_file')

    wf.connect(merge_predictions_wf, 'out_file', 'outputspec', 'out_file')
    wf.connect(merge_predictions_wf, 'out_file', 'sinker', 'pain_predictions')


@BidsPipeline(output_query={
    'T1w': dict(
        datatype='anat',
        suffix="T1w",
        session="1",
        extension=['nii', 'nii.gz']
    ),
    'bold': dict(
        datatype='func',
        suffix="bold",
        session="1",
        task="rest",
        extension=['nii', 'nii.gz']
    )
})
def rcpl(wf, bbr=True, **kwargs):

    print('* bbr:', bbr)

    reorient_struct_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_struct_wf")
    wf.connect('inputspec', 'T1w', reorient_struct_wf, 'in_file')

    reorient_func_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_func_wf")
    wf.connect('inputspec', 'bold', reorient_func_wf, 'in_file')

    anatomical_preprocessing_wf = anat_proc(name='anatomical_preprocessing_wf', bet_tool='deepbet')
    wf.connect(reorient_struct_wf, 'out_file', anatomical_preprocessing_wf, 'in_file')

    func2anat_wf = func2anat(name='func2anat_wf', bbr=bbr)
    wf.connect(reorient_func_wf, 'out_file', func2anat_wf, 'func')
    wf.connect(anatomical_preprocessing_wf, 'brain', func2anat_wf, 'head')
    wf.connect(anatomical_preprocessing_wf, 'probmap_wm', func2anat_wf, 'anat_wm_segmentation')
    wf.connect(anatomical_preprocessing_wf, 'probmap_csf', func2anat_wf, 'anat_csf_segmentation')
    wf.connect(anatomical_preprocessing_wf, 'probmap_gm', func2anat_wf, 'anat_gm_segmentation')
    wf.connect(anatomical_preprocessing_wf, 'probmap_ventricle', func2anat_wf, 'anat_ventricle_segmentation')

    compcor_roi_wf = anat_noise_roi('compcor_roi_wf')
    wf.connect(func2anat_wf, 'wm_mask_in_funcspace', compcor_roi_wf, 'wm_mask')
    wf.connect(func2anat_wf, 'ventricle_mask_in_funcspace', compcor_roi_wf, 'ventricle_mask')

    func_proc_wf = func_proc_despike_afni('func_proc_wf', bet_tool='deepbet', deepbet_n_dilate=2)
    wf.connect(reorient_func_wf, 'out_file', func_proc_wf, 'func')
    wf.connect(compcor_roi_wf, 'out_file', func_proc_wf, 'cc_noise_roi')

    pick_atlas_wf = mist_atlas('pick_atlas_wf')
    mist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_in/atlas/MIST"))
    pick_atlas_wf.get_node('inputspec').inputs.labelmap = os.path.join(mist_dir, 'Parcellations/MIST_122.nii.gz')
    pick_atlas_wf.get_node('inputspec').inputs.modules = mist_modules(mist_directory=mist_dir, resolution="122")
    pick_atlas_wf.get_node('inputspec').inputs.labels = mist_labels(mist_directory=mist_dir, resolution="122")

    extract_timeseries = extract_timeseries_nativespace('extract_timeseries')
    wf.connect(pick_atlas_wf, 'relabeled_atlas', extract_timeseries, 'atlas')
    wf.connect(pick_atlas_wf, 'reordered_labels', extract_timeseries, 'labels')
    wf.connect(pick_atlas_wf, 'reordered_modules', extract_timeseries, 'modules')
    wf.connect(anatomical_preprocessing_wf, 'brain', extract_timeseries, 'anat')
    wf.connect(func2anat_wf, 'anat_to_func_linear_xfm', extract_timeseries, 'inv_linear_reg_mtrx')
    wf.connect(anatomical_preprocessing_wf, 'mni2anat_warpfield', extract_timeseries, 'inv_nonlinear_reg_mtrx')
    wf.connect(func2anat_wf, 'gm_mask_in_funcspace', extract_timeseries, 'gm_mask')
    wf.connect(func_proc_wf, 'func_preprocessed', extract_timeseries, 'func')
    wf.connect(func_proc_wf, 'FD', extract_timeseries, 'confounds')

    func2std = func2standard('func2std')
    wf.connect(anatomical_preprocessing_wf, 'brain', func2std, 'anat')
    wf.connect(func2anat_wf, 'func_to_anat_linear_xfm', func2std, 'linear_reg_mtrx')
    wf.connect(anatomical_preprocessing_wf, 'anat2mni_warpfield', func2std, 'nonlinear_reg_mtrx')
    wf.connect(anatomical_preprocessing_wf, 'std_template', func2std, 'reference_brain')
    wf.connect(func_proc_wf, 'func_preprocessed', func2std, 'func')
    wf.connect(func_proc_wf, 'mc_ref_vol', func2std, 'bbr2ants_source_file')

    calculate_connectivity_wf = calculate_connectivity('calculate_connectivity_wf')
    wf.connect(extract_timeseries, 'timeseries', calculate_connectivity_wf, 'ts_files')
    wf.connect(func_proc_wf, 'FD', calculate_connectivity_wf, 'fd_files')

    predict_pain_sensitivity_rpn_wf = predict_pain_sensitivity_rpn('predict_pain_sensitivity_rpn_wf')
    wf.connect(calculate_connectivity_wf, 'features', predict_pain_sensitivity_rpn_wf, 'X')
    wf.connect('inputspec', 'bold', predict_pain_sensitivity_rpn_wf, 'in_file')

    predict_pain_sensitivity_rcpl_wf = predict_pain_sensitivity_rcpl('predict_pain_sensitivity_rcpl_wf')
    wf.connect(calculate_connectivity_wf, 'features', predict_pain_sensitivity_rcpl_wf, 'X')
    wf.connect('inputspec', 'bold', predict_pain_sensitivity_rcpl_wf, 'in_file')

    collect_pain_predictions_wf = collect_pain_predictions('collect_pain_predictions_wf')
    wf.connect(predict_pain_sensitivity_rpn_wf, 'out_file', collect_pain_predictions_wf, 'rpn_out_file')
    wf.connect(predict_pain_sensitivity_rcpl_wf, 'out_file', collect_pain_predictions_wf, 'rcpl_out_file')

    wf.write_graph('RCPL-pipeline.png')
    create_dataset_description(wf, pipeline_description_name='RCPL-pipeline')


rcpl_app = BidsApp(
    pipeline=rcpl,
    name='rcpl',
    bids_dir='../data_in/ds001907'  # if you pass a cli argument this will be written over!
)
rcpl_app.parser.add_argument(
    '--bbr',
    default='yes',
    type=lambda x: (str(x).lower() in ['true', '1', 'yes']),
    help="Use BBR registration: yes/no (default: yes)"
)

rcpl_app.run()
