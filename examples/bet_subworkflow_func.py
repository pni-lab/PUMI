import sys
from nipype import IdentityInterface, Function
from PUMI.engine import NestedWorkflow as Workflow
from PUMI.engine import NestedNode as Node
from nipype.interfaces import BIDSDataGrabber
from nipype.utils.filemanip import list_to_filename
from PUMI.pipelines.anat.segmentation import bet_fsl
from pipelines.multimodal.image_manipulation import pick_volume
import argparse
import os


'''
Using command line arguments, one can set the paths to the input/output/working directory of the workflow.
Remember to enter a full path.

If nothing was given, default paths will be used.(Might cause Exception)
'''


ROOT_DIR = os.path.dirname(os.getcwd())
input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
output_dir = os.path.join(ROOT_DIR,
                          'data_out')  # path where the folder 'BET' will be created for the results of this script
working_dir = os.path.join(ROOT_DIR,
                           'data_out')  # path where the folder 'bet_iter_wf' will be created for the workflow


# Create command line parser in case user wanted to specify the paths.
parser = argparse.ArgumentParser(description='Using command line arguments, one can optionally set the paths to the '
                                             'input/output/working directory of the workflow.')
parser.add_argument('-input_dir', nargs='?', metavar='input_dir', type=str, default=input_dir,
                    help='Path to Bids-Directory path')
parser.add_argument('-output_dir', nargs='?', metavar='output_dir', type=str, default=output_dir,
                    help='Path to output directory')
parser.add_argument('-working_dir', nargs='?', metavar='working_dir', type=str, default=working_dir,
                    help='Path, where Workflow Data will '
                         'be stored')
args = parser.parse_args()

# subjects for which a brain extraction should be performed
# It needs to be done one after another since images need to be extracted at run time

subjects = ['001']
# subjects = ['002']
# subjects = ['003']

wf = Workflow(name='bet_func_wf')
wf.base_dir = os.path.abspath(args.working_dir)

# create a subroutine (subgraph) for every subject
inputspec = Node(IdentityInterface(fields=['subject']), name='input_node')
inputspec.iterables = [('subject', subjects)]

# get functional images
bids_grabber = Node(BIDSDataGrabber(), name='bids_grabber')
bids_grabber.inputs.base_dir = os.path.abspath(args.input_dir)
bids_grabber.inputs.output_query = {
    'bold': dict(
        subject=subjects,
        datatype='func',
        extension=['nii', 'nii.gz']
    )
}
wf.connect(inputspec, 'subject', bids_grabber, 'subject')

# unpack list from bids_grabber
# bids_grabber returns a list with a string (path to the func image of a subject),
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

# Beaware that we are using a sub-wf, and that's why we use (inputspec/outputspec) to (enter/get) data
# Extract 3D Images from 4D Images
img_extraction_wf = pick_volume('img_extraction_wf', volume='mean')

wf.connect(path_extractor, 'out_file', img_extraction_wf, 'in_file')

# Do the brain extraction
bet_wf = bet_fsl('brain_extraction', )
wf.connect(img_extraction_wf, 'out_file', bet_wf, 'in_file')

wf.run()
wf.write_graph('graph.png')
