import os
from PUMI.pipelines.anat.segmentation import defacing
from nipype import IdentityInterface, Function
from PUMI.engine import NestedWorkflow as Workflow, BidsPipeline
from PUMI.engine import NestedNode as Node

ROOT_DIR = os.path.dirname(os.getcwd())

input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
output_dir = os.path.join(ROOT_DIR,
                          'data_out')  # path where the folder 'BET' will be created for the results of this script
working_dir = os.path.join(ROOT_DIR,
                           'data_out')  # path where the folder 'bet_iter_wf' will be created for the workflow


@BidsPipeline(output_query={  # Defacing will be performed only on anatomical images
    'T1w': dict(
        datatype='anat',
        extension=['nii.gz']
    )
})
def defacing_wf(wf, **kwargs):
    """
     Example for Defacing workflow

     Inputs
     -------
     Path to anatomical image

     Output
     -------
     Mask of the defaced image


    """

    deface_wf = defacing('deface_wf')

    wf.connect('inputspec', 'T1w', deface_wf, 'in_file')

    outputspec = Node(IdentityInterface(fields=['out_file']), name='outputspec')
    wf.connect(deface_wf, 'deface_mask', outputspec, 'out_file')

    wf.write_graph('deface_graph.png')


deface_ex_wf = defacing_wf('deface_ex_wf', base_dir=output_dir, bids_dir=input_dir, subjects=['001'])
