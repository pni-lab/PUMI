import nipype.interfaces.mrtrix3 as mrt
from nipype import Function
from nipype.interfaces.fsl import Reorient2Std

from PUMI.engine import NestedWorkflow as Workflow, BidsPipeline
from PUMI.engine import NestedNode as Node
from nipype.interfaces import BIDSDataGrabber, fsl
import os
import nipype.interfaces.utility as util

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
input_dir = os.path.join(ROOT_DIR, 'data_in/dw_dataset')  # place where the bids data is located
output_dir = os.path.join(ROOT_DIR, 'data_out/derivatives/mrtrix3')
working_dir = os.path.join(ROOT_DIR, 'data_out')


'''input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
output_dir = os.path.join(ROOT_DIR,
                          'data_out')  # path where the folder 'BET' will be created for the results of this script
working_dir = os.path.join(ROOT_DIR,
                           'data_out')  # path where the folder 'bet_iter_wf' will be created for the workflow'''



def eddy(in_file, out_file_path):
    from PUMI.engine import NestedNode as Node
    from nipype.interfaces import fsl

    eddycorrect = Node(fsl.EddyCorrect(), name='ed_correct')
    eddycorrect.inputs.out_file = out_file_path
    eddycorrect.inputs.in_file = in_file

    return out_file_path

def combine_inputs(in1, in2):
    return tuple((in1, in2))


@BidsPipeline(output_query={
                'dwi': dict(datatype='dwi', extension=['nii', 'nii.gz']),
                'bvec': dict(datatype='dwi', suffix='dwi', extension= '.bvec'),
                'bval': dict(datatype='dwi', suffix='dwi', extension='.bval')

})
def dw_processing_wf(wf, **kwargs):

    # Eddy Correct
    ed_correct = Node(fsl.EddyCorrect(), name='ed_correct')
    wf.connect('inputspec', 'dwi', ed_correct, 'in_file')

    grad_fsl = Node(Function(input_names=['in1', 'in2'], output_names=['out'], function=combine_inputs), 'grad_fsl')
    wf.connect('inputspec', 'bvec', grad_fsl, 'in1')
    wf.connect('inputspec', 'bval', grad_fsl, 'in2')

    # Convert to .mif
    mrconvert = Node(mrt.MRConvert(), name='mrconvert')
    wf.connect(ed_correct, 'eddy_corrected', mrconvert, 'in_file')
    wf.connect(grad_fsl, 'out', mrconvert, 'grad_fsl')

    # Denoising
    dwi_denoise = Node(mrt.DWIDenoise(), name='dwi_denoise')
    wf.connect(mrconvert, 'out_file', dwi_denoise, 'in_file')


    # MRDeGibbs
    mrde_gibbs = Node(mrt.MRDeGibbs(), name='mrde_gibbs')
    wf.connect(dwi_denoise, 'out_file', mrde_gibbs, 'in_file')


    # Brain mask of denoised image
    brain_mask = Node(mrt.BrainMask(), name='brain_mask')
    wf.connect(mrde_gibbs, 'out_file', brain_mask, 'in_file')


if __name__ == '__main__':

    # Beaware of the subjects suffixes in the dataset
    dw_processing_wf('dw_processing_wf', base_dir=output_dir, bids_dir=input_dir, subjects=['0001', '0002'])
