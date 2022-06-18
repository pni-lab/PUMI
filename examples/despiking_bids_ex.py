import os
from PUMI.pipelines.anat.segmentation import defacing
from nipype import IdentityInterface, Function
from PUMI.engine import NestedWorkflow as Workflow, BidsPipeline
from PUMI.engine import NestedNode as Node
from pipelines.func.deconfound import despiking_afni

ROOT_DIR = os.path.dirname(os.getcwd())

input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
output_dir = os.path.join(ROOT_DIR,
                          'data_out')  # path where the folder 'BET' will be created for the results of this script
working_dir = os.path.join(ROOT_DIR,
                           'data_out')  # path where the folder 'bet_iter_wf' will be created for the workflow


@BidsPipeline(output_query={  # Despiking will be performed only on anatomical images
    'bold': dict(
        datatype='func',
        extension=['nii', 'nii.gz']
    )
})
def despiking_wf(wf, **kwargs):
    # Create the despiking workflow
    despike_wf = despiking_afni('despike_wf')

    wf.connect('inputspec', 'bold', despike_wf, 'in_file')

    wf.write_graph('despike_graph.png')


despiking_ex_wf = despiking_wf('despiking_ex_wf', base_dir=output_dir, bids_dir=input_dir, subjects=['001'])
