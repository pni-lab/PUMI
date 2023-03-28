from nipype.interfaces.fsl import Reorient2Std
from PUMI.engine import BidsPipeline, NestedNode as Node
from PUMI.pipelines.anat.anat_proc import anat_proc
from PUMI.pipelines.func.compcor import anat_noise_roi, compcor
from PUMI.pipelines.anat.func_to_anat import func2anat
import os
from PUMI.pipelines.func.func_proc import func_proc_despike_afni
from PUMI.pipelines.func.timeseries_extractor import pick_atlas, extract_timeseries_nativespace
from PUMI.utils import mist_modules, mist_labels
from PUMI.pipelines.multimodal.atlas import atlas_selection

ROOT_DIR = os.path.dirname(os.getcwd())

input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
output_dir = os.path.join(ROOT_DIR, 'data_out')  # path for the folder with the results of this script
working_dir = os.path.join(ROOT_DIR, 'data_out')  # path for the workflow folder


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
def rpn_preproc(wf, **kwargs):
    reorient_struct_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_struct_wf")
    wf.connect('inputspec', 'T1w', reorient_struct_wf, 'in_file')

    reorient_func_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_func_wf")
    wf.connect('inputspec', 'bold', reorient_func_wf, 'in_file')

    anatomical_preprocessing_wf = anat_proc(name='anatomical_preprocessing_wf')
    wf.connect(reorient_struct_wf, 'out_file', anatomical_preprocessing_wf, 'in_file')

    bbr_wf = func2anat(name='bbr_wf')
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

    wf.write_graph('rpn_preproc.png')


if __name__ == '__main__':
    rpn_preproc('rpn_preproc', base_dir=output_dir, bids_dir=input_dir, subjects=['001'])
