from nipype import IdentityInterface, Function
from PUMI.engine import NestedWorkflow as Workflow
from PUMI.engine import NestedNode as Node
from nipype.interfaces import BIDSDataGrabber
from nipype.utils.filemanip import list_to_filename
from PUMI.pipelines.anat.segmentation import bet_fsl
from PUMI.pipelines.multimodal.ImgExtraction import img_extraction_workflow
import definitions
import os

# experiment specific parameters:
from pipelines.multimodal import ImgExtraction

input_dir = definitions.BIDS_DIR  # Path to the bids
output_dir = definitions.DATA_OUT_DIR  # End Results of the workflow
working_dir = definitions.DATA_OUT_DIR  # Path, where Workflow Data will be stored

# subjects for which a brain extraction should be performed
# It needs to be done one after another since images need to be extracted at run time

# subjects = ['001']
# subjects = ['002']
subjects = ['003']

wf = Workflow(name='bet_func_wf')
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





# Step 4 : Extract 3D Images from 4D Images


img_extraction_wf = ImgExtraction.img_extraction_workflow(wf_name="img_extraction_wf",
                                                          sink_tag='Sub-00333', volume='first')

wf.connect(path_extractor, 'out_file', img_extraction_wf, 'inputspec.func')

# Step 5: Do the brain extraction
# All PUMI subworkflows take care sinking and qc-ing the most important results
bet_wf = bet_fsl('brain_extraction')
wf.connect(img_extraction_wf, 'outputspec.func_slice', bet_wf, 'in_file')

wf.run()
wf.write_graph('graph.png')
