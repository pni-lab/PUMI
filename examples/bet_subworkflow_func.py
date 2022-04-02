from nipype import IdentityInterface, Function
from PUMI.engine import NestedWorkflow as Workflow
from PUMI.engine import NestedNode as Node
from nipype.interfaces import BIDSDataGrabber, fsl
from nipype.utils.filemanip import list_to_filename
from PUMI.pipelines.anat.segmentation import bet_fsl, bet_hd
from PUMI.interfaces.ImgExtraction import img_extraction
import os


# experiment specific parameters:
# paths relative to PUMI directory not PUMI/scripts
input_dir = 'data_in/bids'  # place where the bids data is located
output_dir = 'data_out'  # place where the folder 'BET' will be created for the results of this script
working_dir = 'data_out'  # place where the folder 'bet_iter_wf' will be created for the workflow

# To make paths realtive to PUMI and not PUMI/examples
os.chdir("..")



# subjects = ['001']  # subjects for which a brain extraction should be performed
# subjects = ['002']
subjects = ['003']


wf = Workflow(name='workflow')
wf.base_dir = os.path.abspath(working_dir)

# create a subroutine (subgraph) for every subject
inputspec = Node(IdentityInterface(fields=['subject']), name='input_node')
inputspec.iterables = [('subject', subjects)]



# get functional images
bids_grabber = Node(BIDSDataGrabber(), name='bids_grabber')
bids_grabber.inputs.base_dir = os.path.abspath(input_dir)
bids_grabber.inputs.output_query = {
    'bold': dict(
        subject=subjects,
        datatype='func',
        extension=['nii', 'nii.gz']
    )
}
wf.connect(inputspec, 'subject', bids_grabber, 'subject')


# unpack list from bids_grabber
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
wf.connect(bids_grabber, 'bold', path_extractor, 'filelist')





# Step 4 : Extract 3D Images from 4D Images



img_extractor = Node(
    Function(
        input_names=['in_img_4d'],
        output_names=['out_img_3d'],
        function=img_extraction
    ),
    name='img_extractor'
)

wf.connect(path_extractor, 'out_file', img_extractor, 'in_img_4d')



# Step 5: Do the brain extraction
# All PUMI subworkflows take care sinking and qc-ing the most important results
bet_wf = bet_hd('brain_extraction')
wf.connect(img_extractor, 'out_img_3d', bet_wf, 'in_file')



wf.run()
wf.write_graph('graph.png')





