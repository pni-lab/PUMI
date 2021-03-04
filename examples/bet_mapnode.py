from nipype import Node, MapNode, Workflow, DataSink
from nipype.interfaces import BIDSDataGrabber, fsl
import os

# experiment specific parameters:
# paths relative to PUMI directory not PUMI/scripts
input_dir = 'data_in/example-bids'  # place where the bids data is located
output_dir = 'data_out'  # place where the folder 'BET' will be created for the results of this script
working_dir = 'data_out'  # place where the folder 'bet_mapnode_wf' will be created for the workflow

subjects = ['001', '002', '003']  # subjects for which a brain extraction should be performed
# ---


# Change current working directory to PUMI, if necessary
if os.getcwd().find('/PUMI/examples') != -1:
    os.chdir('..')

# Step 1: Get anatomical images
bids_grabber = Node(BIDSDataGrabber(), name='bids_grabber')
bids_grabber.inputs.base_dir = os.path.abspath(input_dir)
bids_grabber.inputs.output_query = {
    'T1w': dict(
        subject=subjects,
        datatype='anat',
        extension=['nii', 'nii.gz']
    )
}

# Step 2: Do the brain extraction
bet = MapNode(fsl.BET(), iterfield=['in_file'], name='bet')

# Step 3: Save results
sinker = Node(DataSink(), name='sinker')
sinker.inputs.base_directory = os.path.abspath(output_dir)
sinker.inputs.substitutions = [('_bet', 'result-')]

# Step 4: Start workflow
wf = Workflow(name='bet_mapnode_wf')
wf.base_dir = os.path.abspath(working_dir)
wf.connect([
    (bids_grabber, bet, [('T1w', 'in_file')]),
    (bet, sinker, [('out_file', 'BET')])
])
wf.run()
