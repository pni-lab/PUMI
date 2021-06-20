from nipype import IdentityInterface, Function
from nipype.interfaces.fsl import Reorient2Std
from PUMI.engine import NestedWorkflow as Workflow
from PUMI.engine import NestedNode as Node
from nipype.interfaces import BIDSDataGrabber, fsl
from nipype.utils.filemanip import list_to_filename
from PUMI.pipelines.anat.segmentation import bet_fsl
from PUMI.pipelines.anat.anat2mni import anat2mni_fsl
import os

# experiment specific parameters:
input_dir = 'data_in/example-bids'  # place where the bids data is located
output_dir = 'data_out'  # place where the folder 'BET' will be created for the results of this script
working_dir = 'data_out'  # place where the folder 'bet_iter_wf' will be created for the workflow

subjects = ['001', '002', '003']  # subjects for which a brain extraction should be performed
# ---

wf = Workflow(name='workflow')
wf.base_dir = os.path.abspath(working_dir)

# Create a subroutine (subgraph) for every subject
inputspec = Node(interface=IdentityInterface(fields=['subject']), name='inputspec')
inputspec.iterables = [('subject', subjects)]

# Get anatomical images
bids_grabber = Node(BIDSDataGrabber(), name='bids_grabber')
bids_grabber.inputs.base_dir = os.path.abspath(input_dir)
bids_grabber.inputs.output_query = {
    'T1w': dict(
        subject=subjects,
        datatype='anat',
        extension=['nii', 'nii.gz']
    )
}
wf.connect(inputspec, 'subject', bids_grabber, 'subject')

# 'Unpack' list from bids_grabber
# bids_grabber returns a list with a string (path to the anat image of a subject),
# but fsl.Bet does not take a list as a input file
path_extractor = Node(
    Function(
        input_names=["filelist"],
        output_names=["out_file"],
        function=list_to_filename
    ),
    name="path_extractor_node"
)
wf.connect(bids_grabber, 'T1w', path_extractor, 'filelist')

# reorient images
reorient = Node(interface=Reorient2Std(), name="reorient")
wf.connect(path_extractor, 'out_file', reorient, 'in_file')

# Do the brain extraction
# All PUMI subworkflows take care sinking and qc-ing the most important results
brain_extraction = bet_fsl('brain_extraction')  # todo: use other brain extraction tool
wf.connect(reorient, 'out_file', brain_extraction, 'in_file')

# transform to MNI
anat2mni_wf = anat2mni_fsl('anat2mni')
wf.connect(brain_extraction, 'out_file', anat2mni_wf, 'brain')
wf.connect(reorient, 'out_file', anat2mni_wf, 'head')

# run workflow
wf.run(plugin='MultiProc')
wf.write_graph('graph.png')
