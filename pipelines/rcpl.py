#!/usr/bin/env python3

from nipype.interfaces.fsl import Reorient2Std
from nipype.interfaces import afni
from PUMI.engine import BidsPipeline, NestedNode as Node, FuncPipeline, GroupPipeline, BidsApp, \
    create_dataset_description
from PUMI.pipelines.anat.anat_proc import anat_proc
from PUMI.pipelines.func.compcor import anat_noise_roi, compcor
from PUMI.pipelines.anat.func_to_anat import func2anat
from nipype.interfaces import utility
from PUMI.pipelines.func.func2func import func2func
from PUMI.pipelines.func.deconfound import fieldmap_correction_topup
from PUMI.pipelines.func.func_proc import func_proc_despike_afni
from PUMI.pipelines.func.timeseries_extractor import pick_atlas, extract_timeseries_nativespace
from PUMI.utils import mist_modules, mist_labels, get_reference
from PUMI.pipelines.func.func2standard import func2standard
from PUMI.pipelines.multimodal.image_manipulation import pick_volume
import traits
import os

from PUMI.utils.atlas import relabel_mist_atlas
from PUMI.pipelines.multimodal.atlas import mist_atlas
from PUMI.pipelines.multimodal.pain_prediction import (
    calculate_connectivity,
    predict_pain_sensitivity_rpn,
    predict_pain_sensitivity_rcpl,
    collect_pain_predictions
)


@BidsPipeline(output_query={
    'T1w': dict(
        datatype='anat',
        suffix='T1w',
        extension=['nii', 'nii.gz']
    ),
    'bold': dict(
        datatype='func',
        suffix='bold',
        extension=['nii', 'nii.gz']
    ),
    'bold_json': dict(
        datatype='func',
        suffix='bold',
        extension='.json'
    ),
    'fmap': dict(
        datatype='fmap',
        acquisition='bold',
        suffix='epi',
        extension=['nii', 'nii.gz']
    ),
    'fmap_json': dict(
        datatype='fmap',
        acquisition='bold',
        suffix='epi',
        extension='.json'
    ),
    'sbref': dict(
        datatype='func',
        suffix="sbref",
        extension=['nii', 'nii.gz']
    )
})
def rcpl(wf, bbr=True, **kwargs):

    print('* bbr:', bbr)

    reorient_struct_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_struct_wf")
    wf.connect('inputspec', 'T1w', reorient_struct_wf, 'in_file')

    reorient_func_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_func_wf")
    wf.connect('inputspec', 'bold', reorient_func_wf, 'in_file')

    reorient_fmap_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_fmap_wf")
    wf.connect('inputspec', 'fmap', reorient_fmap_wf, 'in_file')

    reorient_sbref_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_sbref_wf")
    wf.connect('inputspec', 'sbref', reorient_sbref_wf, 'in_file')

    anatomical_preprocessing_wf = anat_proc(name='anatomical_preprocessing_wf', bet_tool='deepbet')
    wf.connect(reorient_struct_wf, 'out_file', anatomical_preprocessing_wf, 'in_file')

    fieldmap_corr = fieldmap_correction_topup('fieldmap_corr')
    wf.connect(reorient_func_wf, 'out_file', fieldmap_corr, 'main')
    wf.connect('inputspec', 'bold_json', fieldmap_corr, 'main_json')
    wf.connect(reorient_fmap_wf, 'out_file', fieldmap_corr, 'fmap')
    wf.connect('inputspec', 'fmap_json', fieldmap_corr, 'fmap_json')

    func2sbref = func2func('func2sbref')
    wf.connect(fieldmap_corr, 'out_file', func2sbref, 'func_1')
    wf.connect(reorient_sbref_wf, 'out_file', func2sbref, 'func_2')

    func2anat_wf = func2anat(name='func2anat_wf', bbr=bbr)
    wf.connect(func2sbref, 'out_file', func2anat_wf, 'func')
    wf.connect(anatomical_preprocessing_wf, 'brain', func2anat_wf, 'head')
    wf.connect(anatomical_preprocessing_wf, 'probmap_wm', func2anat_wf, 'anat_wm_segmentation')
    wf.connect(anatomical_preprocessing_wf, 'probmap_csf', func2anat_wf, 'anat_csf_segmentation')
    wf.connect(anatomical_preprocessing_wf, 'probmap_gm', func2anat_wf, 'anat_gm_segmentation')
    wf.connect(anatomical_preprocessing_wf, 'probmap_ventricle', func2anat_wf, 'anat_ventricle_segmentation')

    compcor_roi_wf = anat_noise_roi('compcor_roi_wf')
    wf.connect(func2anat_wf, 'wm_mask_in_funcspace', compcor_roi_wf, 'wm_mask')
    wf.connect(func2anat_wf, 'ventricle_mask_in_funcspace', compcor_roi_wf, 'ventricle_mask')

    func_proc_wf = func_proc_despike_afni('func_proc_wf', bet_tool='deepbet', deepbet_n_dilate=2)
    wf.connect(func2sbref, 'out_file', func_proc_wf, 'func')
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
    wf.connect(func2sbref, 'out_file', predict_pain_sensitivity_rpn_wf, 'in_file')

    predict_pain_sensitivity_rcpl_wf = predict_pain_sensitivity_rcpl('predict_pain_sensitivity_rcpl_wf')
    wf.connect(calculate_connectivity_wf, 'features', predict_pain_sensitivity_rcpl_wf, 'X')
    wf.connect(func2sbref, 'out_file', predict_pain_sensitivity_rcpl_wf, 'in_file')

    collect_pain_predictions_wf = collect_pain_predictions('collect_pain_predictions_wf')
    wf.connect(predict_pain_sensitivity_rpn_wf, 'out_file', collect_pain_predictions_wf, 'rpn_out_file')
    wf.connect(predict_pain_sensitivity_rcpl_wf, 'out_file', collect_pain_predictions_wf, 'rcpl_out_file')

    wf.write_graph('RCPL-pipeline.png')
    create_dataset_description(wf, pipeline_description_name='RCPL-pipeline')


rcpl_app = BidsApp(
    pipeline=rcpl,
    name='rcpl',
    bids_dir='../data_in/pumi-unittest'  # if you pass a cli argument this will be written over!
)
rcpl_app.parser.add_argument(
    '--bbr',
    default='yes',
    type=lambda x: (str(x).lower() in ['true', '1', 'yes']),
    help="Use BBR registration: yes/no (default: yes)"
)

rcpl_app.run()
