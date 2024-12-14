from nipype import IdentityInterface, Function
from nipype.interfaces.fsl import Reorient2Std
from PUMI.pipelines.anat.anat_proc import anat_proc
from PUMI.engine import NestedWorkflow as Workflow
from PUMI.engine import NestedNode as Node
from PUMI.pipelines.anat.func_to_anat import func2anat
from nipype.interfaces import BIDSDataGrabber
from nipype.utils.filemanip import list_to_filename
import os

# experiment specific parameters:
# paths relative to PUMI directory not PUMI/scripts
ROOT_DIR = os.path.dirname(os.getcwd())
input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # place where the bids data is located
output_dir = os.path.join(ROOT_DIR, 'data_out')  # place where the folder will be created for the results of this script
working_dir = os.path.join(ROOT_DIR, 'data_out')  # place where the folder will be created for the workflow

subjects = ['001']  # subjects for which a brain extraction should be performed
# ---

wf = Workflow(name='workflow')
wf.base_dir = working_dir

# create a subroutine (subgraph) for every subject
inputspec = Node(IdentityInterface(fields=['subject']), name='input_node')
inputspec.iterables = [('subject', subjects)]

# get anatomical and functional images
bids_grabber = Node(BIDSDataGrabber(), name='bids_grabber')
bids_grabber.inputs.base_dir = input_dir
bids_grabber.inputs.output_query = {
    'T1w': dict(
        subject=subjects,
        datatype='anat',
        extension=['nii.gz']
    ),
    'bold': dict(
        subject=subjects,
        datatype='func',
        extension=['nii', 'nii.gz']
    )
}
wf.connect(inputspec, 'subject', bids_grabber, 'subject')

path_extractor_anat = Node(
    Function(input_names=["filelist"], output_names=["out_file"], function=list_to_filename), name="path_extractor_anat"
)
wf.connect(bids_grabber, 'T1w', path_extractor_anat, 'filelist')

path_extractor_func = Node(
    Function(input_names=["filelist"], output_names=["out_file"], function=list_to_filename), name="path_extractor_func"
)
wf.connect(bids_grabber, 'bold', path_extractor_func, 'filelist')

# reorient anat images
reorient_anat = Node(interface=Reorient2Std(), name="reorient_anat")
reorient_anat.inputs.output_type = 'NIFTI_GZ'
wf.connect(path_extractor_anat, 'out_file', reorient_anat, 'in_file')

# reorient func images
reorient_func = Node(interface=Reorient2Std(), name="reorient_func")
reorient_func.inputs.output_type = 'NIFTI_GZ'
wf.connect(path_extractor_func, 'out_file', reorient_func, 'in_file')

anat_proc = anat_proc('brain_extraction')
wf.connect(reorient_anat, 'out_file', anat_proc, 'in_file')

bbr = func2anat('func2anat')
wf.connect(reorient_func, 'out_file', bbr, 'func')
wf.connect(anat_proc, 'brain', bbr, 'head')  # todo: rename head to brain if everytime brain should be passed
wf.connect(anat_proc, 'probmap_wm', bbr, 'anat_wm_segmentation')
wf.connect(anat_proc, 'probmap_gm', bbr, 'anat_gm_segmentation')
wf.connect(anat_proc, 'probmap_csf', bbr, 'anat_csf_segmentation')
wf.connect(anat_proc, 'probmap_ventricle', bbr, 'anat_ventricle_segmentation')


wf.run(plugin='MultiProc')
wf.write_graph('graph.png')
