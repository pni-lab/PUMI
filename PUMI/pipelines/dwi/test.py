import nipype.interfaces.mrtrix3 as mrt
from nipype import Function
from nipype.interfaces.fsl import Reorient2Std

from PUMI.engine import NestedWorkflow as Workflow, BidsPipeline
from PUMI.engine import NestedNode as Node
from nipype.interfaces import BIDSDataGrabber, fsl
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
input_dir = os.path.join(ROOT_DIR, 'data_in/dw_dataset')  # place where the bids data is located
output_dir = os.path.join(ROOT_DIR, 'data_out/derivatives/mrtrix3')
working_dir = os.path.join(ROOT_DIR, 'data_out')


'''input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
output_dir = os.path.join(ROOT_DIR,
                          'data_out')  # path where the folder 'BET' will be created for the results of this script
working_dir = os.path.join(ROOT_DIR,
                           'data_out')  # path where the folder 'bet_iter_wf' will be created for the workflow'''



print(ROOT_DIR)
print(input_dir)

def eddy(in_file, out_file_path):
    from PUMI.engine import NestedNode as Node
    from nipype.interfaces import fsl

    eddycorrect = Node(fsl.EddyCorrect(), name='ed_correct')
    eddycorrect.inputs.out_file = out_file_path
    eddycorrect.inputs.in_file = in_file

    return out_file_path

@BidsPipeline(output_query={
                'dwi': dict(
                    datatype='dwi',
                    extension=['nii', 'nii.gz']
                )
})
def dw_processing_wf(wf, **kwargs):

    # in_file =  'sub-0002/dwi/sub-0002_dwi.nii.gz'
    out_file = 'sub-0002_dwi_eddy-correct.nii.gz'

    wf.base_dir = working_dir

    # Eddy Correct
    ed_correct = Node(Function(input_names=['in_file', 'out_file_path'],
                               output_names=['out_file'],
                               function=eddy), name='ed_correct')

    ed_correct.inputs.out_file_path = os.path.join(output_dir, out_file)

    wf.connect('inputspec', 'dwi', ed_correct, 'in_file')


    # Convert to .mif
    mrconvert = Node(mrt.MRConvert(), name='mrconvert')
    mrconvert.inputs.grad_fsl = (os.path.join(input_dir, 'sub-0002/dwi/sub-0002_dwi.bvec'),
                                 os.path.join(input_dir,'sub-0002/dwi/sub-0002_dwi.bval'))
    mrconvert.inputs.out_file = os.path.join(output_dir,'sub-0002_dwi_eddy-correct.mif')


    wf.connect(ed_correct, 'out_file', mrconvert, 'in_file')


    # Denoising
    dwi_denoise = Node(mrt.DWIDenoise(), name='dwi_denoise')
    # dwi_denoise.inputs.in_file = os.path.join(output_dir, 'sub-0002_dwi_eddy-correct.mif')
    dwi_denoise.inputs.out_file = os.path.join(output_dir, 'sub-002_dwi_eddy-correct_dwidenoise.mif')
    # dwi_denoise.run()

    wf.connect(mrconvert, 'out_file', dwi_denoise, 'in_file')


if __name__ == '__main__':
    dw_processing_wf('dw_processing_wf', base_dir=output_dir, bids_dir=input_dir, subjects=['0001'])



'''
    # MRDeGibbs
    mrde_gibbs = Node(mrt.MRDeGibbs(), name='mrde_gibbs')
    mrde_gibbs.inputs.in_file = os.path.join(output_dir, 'sub-002_dwi_eddy-correct_dwidenoise.mif')
    mrde_gibbs.inputs.out_file = os.path.join(output_dir, 'sub-002_dwi_eddy-correct_dwidenoise_degibbs.mif')
    mrde_gibbs.run()


    # Create a brain mask of denoised image
    brain_mask = Node(mrt.BrainMask(), name='brain_mask')
    brain_mask.inputs.in_file = os.path.join(output_dir,'sub-0002_dwi_eddy-correct.mif')
    brain_mask.inputs.out_file = os.path.join(output_dir, 'sub-0002_dwi_eddy-correct_dwidenoise_mask.mif')
    brain_mask.run()

'''