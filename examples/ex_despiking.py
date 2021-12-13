from nipype import IdentityInterface, Function
from PUMI.engine import NestedWorkflow as Workflow
from PUMI.engine import NestedNode as Node
from nipype.interfaces import BIDSDataGrabber
from nipype.utils.filemanip import list_to_filename
import os
from PUMI.pipelines.func.deconfound import despiking_afni




input_dir = 'data_in/bids'
output_dir = 'data_out'
working_dir = 'data_out'


subjects = ['001', '002', '003']


despiking_wf = Workflow("despiking_wf")
despiking_wf.base_dir = os.path.abspath(working_dir)

inputspec = Node(interface=IdentityInterface(fields=['subject']), name='inputspec')
inputspec.iterables = [('subject', subjects)]


# Get functional images
bids_grabber = Node(BIDSDataGrabber(), name='bids_grabber')
bids_grabber.inputs.base_dir = os.path.abspath(input_dir)
bids_grabber.inputs.output_query = {
    'T1w': dict(
        subject=subjects,
        datatype='func',
        extension=['nii', 'nii.gz']
    )
}

despiking_wf.connect(inputspec, 'subject', bids_grabber, 'subject')

path_extractor = Node(
    Function(
        input_names=["filelist"],
        output_names=["out_file"],
        function=list_to_filename
    ),
    name="path_extractor_node"
)


despiking_wf.connect(bids_grabber, 'T1w', path_extractor, 'filelist')


despike = despiking_afni('despiker')
despiking_wf.connect(path_extractor, 'out_file', despike, 'in_file')

despiking_wf.run(plugin='MultiProc')
despiking_wf.write_graph('graph.png')