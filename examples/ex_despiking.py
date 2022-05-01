from nipype import IdentityInterface, Function

import definitions
from PUMI.engine import NestedWorkflow as Workflow
from PUMI.engine import NestedNode as Node
from nipype.interfaces import BIDSDataGrabber
from nipype.utils.filemanip import list_to_filename
import os
from PUMI.pipelines.func.deconfound import despiking_afni



input_dir = definitions.BIDS_DIR # Path to the bids
output_dir = definitions.DATA_OUT_DIR  # End Results of the workflow
working_dir = definitions.DATA_OUT_DIR # Path, where Workflow Data will be stored


subjects = ['001', '002', '003']


despiking_wf = Workflow("despiking_wf")
despiking_wf.base_dir = os.path.abspath(working_dir)

inputspec = Node(interface=IdentityInterface(fields=['subject']), name='inputspec')
inputspec.iterables = [('subject', subjects)]  # so that we don't have to run the workflow for each subject separately



# Despiking is only relevant for functional imaging, which is (mostly) done by the so-called 'bold' sequence.
# Get functional images
bids_grabber = Node(BIDSDataGrabber(), name='bids_grabber')
bids_grabber.inputs.base_dir = os.path.abspath(input_dir)
bids_grabber.inputs.output_query = {
    'bold': dict(
        subject=subjects,
        datatype='func',
        extension=['nii', 'nii.gz']
    )
}

despiking_wf.connect(inputspec, 'subject', bids_grabber, 'subject')



# 'Unpack' list from bids_grabber
# bids_grabber returns a list with a string (path to the func image of a subject),
path_extractor = Node(
    Function(
        input_names=["filelist"],
        output_names=["out_file"],
        function=list_to_filename
    ),
    name="path_extractor_node"
)


despiking_wf.connect(bids_grabber, 'bold', path_extractor, 'filelist')


despike = despiking_afni('despike')
despiking_wf.connect(path_extractor, 'out_file', despike, 'in_file')

despiking_wf.run(plugin='MultiProc')
despiking_wf.write_graph('graph.png')
