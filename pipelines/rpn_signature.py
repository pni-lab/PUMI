from nipype.interfaces.fsl import Reorient2Std

import PUMI
from PUMI.engine import BidsPipeline, NestedNode as Node, FuncPipeline, GroupPipeline, BidsApp
from PUMI.pipelines.anat.anat_proc import anat_proc
from PUMI.pipelines.func.compcor import anat_noise_roi, compcor
from PUMI.pipelines.anat.func_to_anat import bbr
from nipype.interfaces import utility
import os
from PUMI.pipelines.func.func_proc import func_proc_despike_afni
from PUMI.pipelines.func.timeseries_extractor import pick_atlas, extract_timeseries_nativespace
from PUMI.utils import mist_modules, mist_labels
import traits
from PUMI.pipelines.multimodal.atlas import atlas_selection


@FuncPipeline(inputspec_fields=['ts_files', 'fd_files', 'scrub_threshold'],
              outputspec_fields=['features', 'out_file'])
def calculate_connectivity(wf, **kwargs):
    # Calculate RPN-score: prediction of pain sensitivity
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
        print('42 -- path --', path)
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


@FuncPipeline(inputspec_fields=['X', 'in_files'],
              outputspec_fields=['pred_file'])
def predict_pain_sensitivity(wf, model_json=None, **kwargs):
    """
    If model_json is None -> search for model_json file. Only works when used in PUMI node.
    """
    def predict(X, in_files, model_json):
        from PUMI.utils import rpn_model
        import pandas as pd
        import PUMI
        import os

        if model_json is None:
            #pos = os.getcwd().rindex('PUMI/') + 5
            #model_json = os.getcwd()[0:pos] + 'data_in/rpn_model.json'
            model_json = os.path.dirname(PUMI.__file__) + '/../data_in/rpn_model.json'

        model = rpn_model(file=model_json)
        predicted = model.predict(X)

        path = os.path.abspath('rpn-prediction.csv')
        df = pd.DataFrame()
        df['in_file'] = [in_files]  # todo: originally: df['in_file'] = in_files
        df['RPN'] = predicted
        df.to_csv(path)
        return path

    predict_wf = Node(
        utility.Function(
            input_names=['X', 'in_files', 'model_json'],
            output_names=['out_file'],
            function=predict
        ),
        name="predict_wf"
    )
    wf.connect('inputspec', 'X', predict_wf, 'X')
    wf.connect('inputspec', 'in_files', predict_wf, 'in_files')
    predict_wf.inputs.model_json = model_json

    wf.connect(predict_wf, 'out_file', 'outputspec', 'pred_file')
    wf.connect(predict_wf, 'out_file', 'sinker', 'rpn')


def collect_predictions(wf):
    import pandas as pd
    import glob

    predictions = glob.glob(wf.sink_dir + '/**/rpn-prediction.csv', recursive=True)

    print('42 -- ', wf.sink_dir)
    df = pd.read_csv(predictions[0], index_col=0)
    if len(predictions) > 1:
        for i in range(1, len(predictions)+1):
            other_df = pd.read_csv(predictions[i], index_col=0)
            df.append(other_df)
    df.to_csv(wf.sink_dir + '/predictions.csv')


@BidsPipeline(output_query={
    'T1w': dict(
        datatype='anat',
        extension=['nii', 'nii.gz']
    ),
    'bold': dict(
        datatype='func',
        extension=['nii', 'nii.gz']
    )
})
def rpn(wf, **kwargs):
    reorient_struct_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_struct_wf")
    wf.connect('inputspec', 'T1w', reorient_struct_wf, 'in_file')

    reorient_func_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_func_wf")
    wf.connect('inputspec', 'bold', reorient_func_wf, 'in_file')

    anatomical_preprocessing_wf = anat_proc(name='anatomical_preprocessing_wf')
    wf.connect(reorient_struct_wf, 'out_file', anatomical_preprocessing_wf, 'in_file')

    bbr_wf = bbr(name='bbr_wf')
    wf.connect(reorient_func_wf, 'out_file', bbr_wf, 'func')
    wf.connect(anatomical_preprocessing_wf, 'brain', bbr_wf, 'head')
    wf.connect(anatomical_preprocessing_wf, 'probmap_wm', bbr_wf, 'anat_wm_segmentation')
    wf.connect(anatomical_preprocessing_wf, 'probmap_csf', bbr_wf, 'anat_csf_segmentation')
    wf.connect(anatomical_preprocessing_wf, 'probmap_gm', bbr_wf, 'anat_gm_segmentation')
    wf.connect(anatomical_preprocessing_wf, 'probmap_ventricle', bbr_wf, 'anat_ventricle_segmentation')

    compcor_roi_wf = anat_noise_roi('compcor_roi_wf')
    wf.connect(bbr_wf, 'wm_mask_in_funcspace', compcor_roi_wf, 'wm_mask')
    wf.connect(bbr_wf, 'ventricle_mask_in_funcspace', compcor_roi_wf, 'ventricle_mask')

    func_proc_wf = func_proc_despike_afni('func_proc_wf')
    wf.connect(reorient_func_wf, 'out_file', func_proc_wf, 'func')
    wf.connect(compcor_roi_wf, 'out_file', func_proc_wf, 'cc_noise_roi')

    atlas_selection_wf = atlas_selection('atlas_selection_wf', modularize=True, module_threshold=0.0)
    atlas_selection_wf.get_node('inputspec').inputs.atlas = 'basc'
    atlas_selection_wf.get_node('inputspec').inputs.atlas_params = {}
    atlas_selection_wf.get_node('inputspec').inputs.labelmap_params = ('122',)
    atlas_selection_wf.get_node('inputspec').inputs.modules_atlas = 'basc'
    atlas_selection_wf.get_node('inputspec').inputs.modules_params = {}
    atlas_selection_wf.get_node('inputspec').inputs.modules_labelmap_params = ('7',)

    extract_timeseries = extract_timeseries_nativespace('extract_timeseries')
    wf.connect(atlas_selection_wf, 'labelmap', extract_timeseries, 'atlas')
    wf.connect(atlas_selection_wf, 'labels', extract_timeseries, 'labels')
    wf.connect(atlas_selection_wf, 'modules', extract_timeseries, 'modules')
    wf.connect(anatomical_preprocessing_wf, 'brain', extract_timeseries, 'anat')
    wf.connect(bbr_wf, 'anat_to_func_linear_xfm', extract_timeseries, 'inv_linear_reg_mtrx')
    wf.connect(anatomical_preprocessing_wf, 'mni2anat_warpfield', extract_timeseries, 'inv_nonlinear_reg_mtrx')
    wf.connect(bbr_wf, 'gm_mask_in_funcspace', extract_timeseries, 'gm_mask')
    wf.connect(func_proc_wf, 'func_preprocessed', extract_timeseries, 'func')
    wf.connect(func_proc_wf, 'FD', extract_timeseries, 'confounds')

    calculate_connectivity_wf = calculate_connectivity('calculate_connectivity_wf')
    wf.connect(extract_timeseries, 'timeseries', calculate_connectivity_wf, 'ts_files')
    wf.connect(func_proc_wf, 'FD', calculate_connectivity_wf, 'fd_files')

    predict_pain_sensitivity_wf = predict_pain_sensitivity('predict_pain_sensitivity_wf')
    wf.connect(calculate_connectivity_wf, 'features', predict_pain_sensitivity_wf, 'X')
    wf.connect('inputspec', 'bold', predict_pain_sensitivity_wf, 'in_files')

    wf.write_graph('rpn-signature.png')


rpn_app = BidsApp(
    pipeline=rpn,
    name='rpn',
    bids_dir='../data_in/pumi-unittest'  # if you pass a cli argument this will be written over!
).run()