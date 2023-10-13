from nipype.interfaces.fsl import Reorient2Std
from PUMI.engine import BidsPipeline, NestedNode as Node, BidsApp
from PUMI.pipelines.anat.segmentation import bet_deepbet

@BidsPipeline(output_query={
    'T1w': dict(
        datatype='anat',
        extension=['nii', 'nii.gz']
    ),
    'bold': dict(
        datatype='func',
        extension=['nii.gz', 'nii']
    )
})
def deepbet_wf(wf, **kwargs):

    reorient_struct_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_struct_wf")
    wf.connect('inputspec', 'T1w', reorient_struct_wf, 'in_file')

    anat_bet = bet_deepbet('anat_brain_extraction')
    wf.connect(reorient_struct_wf, 'out_file', anat_bet, 'in_file')


    reorient_func_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_func_wf")
    wf.connect('inputspec', 'bold', reorient_func_wf, 'in_file')

    func_bet = bet_deepbet('func_brain_extraction', fmri=True)
    wf.connect(reorient_func_wf, 'out_file', func_bet, 'in_file')


deepbet_app = BidsApp(
    pipeline=deepbet_wf,
    name='deepbet_wf',
    bids_dir='../data_in/pumi-unittest'  # if you pass a cli argument this will be written over!
)
deepbet_app.run()
