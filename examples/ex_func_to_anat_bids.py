from nipype import IdentityInterface, Function
from nipype.interfaces.fsl import Reorient2Std

from PUMI.engine import NestedWorkflow as Workflow, BidsPipeline
from PUMI.engine import NestedNode as Node

from nipype.interfaces import BIDSDataGrabber
from nipype.utils.filemanip import list_to_filename
import os

# experiment specific parameters:
ROOT_DIR = os.path.dirname(os.getcwd())
input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # place where the bids data is located
output_dir = os.path.join(ROOT_DIR, 'data_out')  # place where the folder will be created for the results of this script
working_dir = os.path.join(ROOT_DIR, 'data_out')  # place where the folder will be created for the workflow


@BidsPipeline(output_query={
    'T1w': dict(
        datatype='anat',
        extension=['nii.gz']
    ),
    'bold': dict(
        datatype='func',
        extension=['nii', 'nii.gz']
    )
})
def func_to_anat_wf(wf, **kwargs):
    from PUMI.pipelines.anat.anat_proc import anat_proc
    from PUMI.pipelines.anat.func_to_anat import bbr


    # reorient anat images
    reorient_anat = Node(interface=Reorient2Std(), name="reorient_anat")
    reorient_anat.inputs.output_type = 'NIFTI_GZ'
    wf.connect('inputspec', 'T1w', reorient_anat, 'in_file')

    # reorient func images
    reorient_func = Node(interface=Reorient2Std(), name="reorient_func")
    reorient_func.inputs.output_type = 'NIFTI_GZ'
    wf.connect('inputspec', 'bold', reorient_func, 'in_file')

    anat_proc = anat_proc('brain_extraction')
    wf.connect(reorient_anat, 'out_file', anat_proc, 'in_file')

    bbr = bbr('bbr')
    wf.connect(reorient_func, 'out_file', bbr, 'func')
    wf.connect(anat_proc, 'brain', bbr, 'head')  # todo: rename head to brain if everytime brain should be passed
    wf.connect(anat_proc, 'probmap_wm', bbr, 'anat_wm_segmentation')
    wf.connect(anat_proc, 'probmap_gm', bbr, 'anat_gm_segmentation')
    wf.connect(anat_proc, 'probmap_csf', bbr, 'anat_csf_segmentation')
    wf.connect(anat_proc, 'probmap_ventricle', bbr, 'anat_ventricle_segmentation')


func_to_anat_wf = func_to_anat_wf('func_to_anat_wf', bids_dir=input_dir, base_dir=working_dir,
                                  output_dir=output_dir, subjects=['002'])
