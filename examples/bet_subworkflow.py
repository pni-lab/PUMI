from nipype import IdentityInterface, Function
from PUMI.engine import NestedWorkflow as Workflow
from PUMI.engine import NestedNode as Node
from nipype.interfaces import BIDSDataGrabber
from nipype.utils.filemanip import list_to_filename
from PUMI.pipelines.anat.segmentation import bet_fsl
import os

# experiment specific parameters:
# paths relative to PUMI directory not PUMI/scripts
input_dir = 'data_in/example-bids'  # place where the bids data is located
output_dir = 'data_out'  # place where the folder 'BET' will be created for the results of this script
working_dir = 'data_out'  # place where the folder 'bet_iter_wf' will be created for the workflow

subjects = ['001', '002', '003']  # subjects for which a brain extraction should be performed
# ---


# Change current working directory to PUMI, if necessary
if os.getcwd().find('/PUMI_new/examples') != -1:
    os.chdir('..')

# Step 1: Create a subroutine (subgraph) for every subject
inputspec = Node(IdentityInterface(fields=['subject']), name='input_node')
inputspec.iterables = [('subject', subjects)]

# Step 2: Get anatomical images
bids_grabber = Node(BIDSDataGrabber(), name='bids_grabber')
bids_grabber.inputs.base_dir = os.path.abspath(input_dir)
bids_grabber.inputs.output_query = {
    'T1w': dict(
        subject=subjects,
        datatype='anat',
        extension=['nii', 'nii.gz']
    )
}

# Step 3: 'Unpack' list from bids_grabber
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

# Step 4: Do the brain extraction
# All PUMI subworkflows take care sinking and qc-ing the most important results
bet_wf = bet_fsl('brain_extraction', qc_dir=os.path.abspath(working_dir) + '/qc',
                 sink_dir=os.path.abspath(working_dir) + '/derivatives')

# Step 6: Start workflow
wf = Workflow(name='workflow')
wf.base_dir = os.path.abspath(working_dir)
wf.connect([
    (inputspec, bids_grabber, [('subject', 'subject')]),
    (bids_grabber, path_extractor, [('T1w', 'filelist')]),
    (path_extractor, bet_wf, [('out_file', 'in_file')])
])

wf.run(plugin='MultiProc')
wf.write_graph('graph.png')
