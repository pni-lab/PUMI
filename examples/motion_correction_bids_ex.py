import os
from nipype.interfaces.fsl import Reorient2Std
from PUMI.engine import BidsPipeline
from PUMI.engine import NestedNode as Node
from PUMI.pipelines.func.deconfound import motion_correction_mcflirt

ROOT_DIR = os.getcwd()

input_dir = os.path.join(ROOT_DIR, 'data_in/pumi-unittest')  # path where the bids data is located
output_dir = os.path.join(ROOT_DIR,
                          'data_out')  # path where the output-folder will be created (the results)
working_dir = os.path.join(ROOT_DIR,
                           'data_out')  # path where the folder workflow-folder will be created


@BidsPipeline(output_query={
    'bold': dict(
        datatype='func',
        extension=['nii', 'nii.gz']
    )
})
def mc_wf(wf, **kwargs):
    reorient = Node(Reorient2Std(), name='reorient')
    wf.connect('inputspec', 'bold', reorient, 'in_file')

    mc = motion_correction_mcflirt('mc')
    wf.connect(reorient, 'out_file', mc, 'in_file')

    wf.write_graph('despike_graph.png')


mc_ex_wf = mc_wf('mc_ex_wf', base_dir=output_dir, bids_dir=input_dir, subjects=['001'])
