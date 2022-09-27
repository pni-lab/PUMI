from nipype.interfaces.fsl import Reorient2Std
from PUMI.engine import BidsPipeline, NestedNode as Node
from PUMI.pipelines.anat.anat_proc import anat_proc
from PUMI.pipelines.func.compcor import anat_noise_roi, compcor
from PUMI.pipelines.anat.func_to_anat import bbr
from nipype.interfaces import utility
import os

from PUMI.pipelines.func.func_proc import func_proc_despike_afni
from PUMI.pipelines.func.timeseries_extractor import pick_atlas, extract_timeseries_nativespace
from PUMI.utils import mist_modules, mist_labels

ROOT_DIR = os.path.dirname(os.getcwd())

input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
#input_dir = os.path.join(ROOT_DIR, 'data_in/pumi-unittest')  # path where the bids data is located
output_dir = os.path.join(ROOT_DIR, 'data_out')  # path for the folder with the results of this script
working_dir = os.path.join(ROOT_DIR, 'data_out')  # path for the workflow folder


def calculate_connectivity(ts_files, fd_files, scrub_threshold=0.15):
    # Calculate RPN-score: prediction of pain sensitivity

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

    mot_file = "motion.csv"
    df.to_csv(mot_file)

    return features, os.path.abspath(mot_file)


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

    pick_atlas_wf = pick_atlas('pick_atlas_wf')
    mist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_in/atlas/MIST"))
    pick_atlas_wf.get_node('inputspec').inputs.labelmap = os.path.join(mist_dir, 'Parcellations/MIST_122.nii.gz')
    pick_atlas_wf.get_node('inputspec').inputs.modules = mist_modules(mist_directory=mist_dir, resolution="122")
    pick_atlas_wf.get_node('inputspec').inputs.labels = mist_labels(mist_directory=mist_dir, resolution="122")

    extract_timeseries = extract_timeseries_nativespace('extract_timeseries')
    wf.connect(pick_atlas_wf, 'relabeled_atlas', extract_timeseries, 'atlas')
    wf.connect(pick_atlas_wf, 'reordered_labels', extract_timeseries, 'labels')
    wf.connect(pick_atlas_wf, 'reordered_modules', extract_timeseries, 'modules')
    wf.connect(anatomical_preprocessing_wf, 'brain', extract_timeseries, 'anat')
    wf.connect(bbr_wf, 'anat_to_func_linear_xfm', extract_timeseries, 'inv_linear_reg_mtrx')
    wf.connect(anatomical_preprocessing_wf, 'mni2anat_warpfield', extract_timeseries, 'inv_nonlinear_reg_mtrx')
    wf.connect(bbr_wf, 'gm_mask_in_funcspace', extract_timeseries, 'gm_mask')
    wf.connect(func_proc_wf, 'func_preprocessed', extract_timeseries, 'func')
    wf.connect(func_proc_wf, 'FD', extract_timeseries, 'confounds')

    calculate_connectivity_wf = Node(
        utility.Function(
            input_names=['ts_files', 'fd_files'],
            output_names=['features', 'motion'],
            function=calculate_connectivity
        ),
        name="calculate_connectivity"
    )
    wf.connect(extract_timeseries, 'timeseries', calculate_connectivity_wf, 'ts_files')
    wf.connect(func_proc_wf, 'FD', calculate_connectivity_wf, 'fd_files')

    wf.write_graph('rpn-signature.png')

print("Starting RPN-signature...")
rpn('rpn', base_dir=output_dir, bids_dir=input_dir, subjects=['001', '002'])
#rpn('rpn', base_dir=output_dir, bids_dir=input_dir, subjects=['001'])
