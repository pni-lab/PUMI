#!/usr/bin/env python3

"""
This pipeline generates connectivity matrizes!
"""

from nipype.interfaces.fsl import Reorient2Std
from nipype.interfaces import afni
from PUMI.engine import BidsPipeline, NestedNode as Node, GroupPipeline, BidsApp
from PUMI.pipelines.anat.anat_proc import anat_proc
from PUMI.pipelines.func.compcor import anat_noise_roi
from PUMI.pipelines.anat.func_to_anat import func2anat
from nipype.interfaces import utility
from PUMI.pipelines.func.connectivity import create_connectivity_matrix
from PUMI.pipelines.func.func_proc import func_proc_despike_afni
from PUMI.pipelines.func.timeseries_extractor import pick_atlas, extract_timeseries_nativespace
from PUMI.utils import mist_modules, mist_labels, get_reference
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
def conn_matrix(wf, **kwargs):
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
    wf.connect(bbr_wf, 'anat_to_func_linear_xfm', extract_timeseries, 'inv_linear_reg_mtrx')
    wf.connect(anatomical_preprocessing_wf, 'mni2anat_warpfield', extract_timeseries, 'inv_nonlinear_reg_mtrx')
    wf.connect(bbr_wf, 'gm_mask_in_funcspace', extract_timeseries, 'gm_mask')
    wf.connect(func_proc_wf, 'func_preprocessed', extract_timeseries, 'func')
    wf.connect(func_proc_wf, 'FD', extract_timeseries, 'confounds')

    create_connectivity_matrix_wf = create_connectivity_matrix('create_connectivity_matrix_wf')
    wf.connect(extract_timeseries, 'timeseries', create_connectivity_matrix_wf, 'ts_file')
    wf.connect(func_proc_wf, 'FD', create_connectivity_matrix_wf, 'fd_file')
    wf.connect(pick_atlas_wf, 'reordered_labels', create_connectivity_matrix_wf, 'atlas_labels')

    wf.write_graph('graph.png')


conn_matrix_app = BidsApp(
    pipeline=conn_matrix,
    name='conn_matrix_wf',
    bids_dir='../data_in/pumi-unittest'  # if you pass a cli argument this will be written over!
).run()