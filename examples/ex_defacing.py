import argparse
import os
from nipype.interfaces import BIDSDataGrabber
from nipype.utils.filemanip import list_to_filename

from PUMI.pipelines.multimodal.I_deface import defacing
from nipype import IdentityInterface, Function
from PUMI.engine import NestedWorkflow as Workflow
from PUMI.engine import NestedNode as Node
import shutil

ROOT_DIR = os.path.dirname(os.getcwd())

input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
output_dir = os.path.join(ROOT_DIR,
                          'data_out')  # path where the folder 'BET' will be created for the results of this script
# sinking data
working_dir = os.path.join(ROOT_DIR,
                           'data_out')  # path where the folder 'bet_iter_wf' will be created for the workflow



defacing_wf = Workflow(name='defacing_wf')
defacing_wf.base_dir = os.path.abspath(working_dir)

subjects = ['001']

# create a subroutine (subgraph) for every subject
inputspec = Node(IdentityInterface(fields=['subject']), name='inputspec')
inputspec.iterables = [('subject', subjects)]


bids_grabber = Node(BIDSDataGrabber(), name='bids_grabber')
bids_grabber.inputs.base_dir = os.path.abspath(input_dir)
bids_grabber.inputs.output_query = {
    'T1w': dict(
        subject=subjects,
        datatype='anat',
        extension=['nii.gz']
    )
}

# Create the defacing workflow
deface = defacing('deface')

defacing_wf.connect(inputspec, 'subject', bids_grabber, 'subject')


# unpack list from bids_grabber
# bids_grabber returns a list with a string (path to the anat image of a subject),
# but padeface does not take a list as a input file
path_extractor = Node(
    Function(
        input_names=["filelist"],
        output_names=["out_file"],
        function=list_to_filename
    ),
    name="path_extractor_node"
)
defacing_wf.connect(bids_grabber, 'T1w', path_extractor, 'filelist')


defacing_wf.connect(path_extractor, 'out_file', deface, 'in_file')

outputspec = Node(IdentityInterface(fields=['out_file']), name='outputspec')

defacing_wf.connect(deface, 'out_file', outputspec, 'out_file')

defacing_wf.run()
defacing_wf.write_graph('deface_graph.png')


