import nipype.interfaces.mrtrix3 as mrt
from PUMI.engine import NestedWorkflow as Workflow
from PUMI.engine import NestedNode as Node
from nipype.interfaces import BIDSDataGrabber, fsl
import os



ROOT_DIR = os.path.dirname(os.getcwd())
input_dir = os.path.join(ROOT_DIR, 'data_in/dw_dataset')  # place where the bids data is located
output_dir = os.path.join(ROOT_DIR, 'data_out/derivatives/mrtrix3')
working_dir = os.path.join(ROOT_DIR, 'data_out')  

in_file =  'sub-0002/dwi/sub-0002_dwi.nii.gz'
out_file = 'sub-0002_dwi_eddy-correct.nii.gz'

wf = Workflow(name='workflow')
wf.base_dir = os.path.abspath(working_dir)



# Eddy Correct
ed_correct = Node(fsl.EddyCorrect(), name='ed_correct', )
ed_correct.inputs.in_file = os.path.join(input_dir, in_file)
ed_correct.inputs.out_file = os.path.join(output_dir, out_file)
ed_correct.run()


# Convert to .mif
mrconvert = Node(mrt.MRConvert(), name='mrconvert')
mrconvert.inputs.in_file = ed_correct.inputs.out_file
mrconvert.inputs.grad_fsl = (os.path.join(input_dir, 'sub-0002/dwi/sub-0002_dwi.bvec'), os.path.join(input_dir,'sub-0002/dwi/sub-0002_dwi.bval'))
mrconvert.inputs.out_file = os.path.join(output_dir,'sub-0002_dwi_eddy-correct.mif')
mrconvert.run()


# Denoising
dwi_denoise = Node(mrt.DWIDenoise(), name='dwi_denoise')
dwi_denoise.inputs.in_file = os.path.join(output_dir, 'sub-0002_dwi_eddy-correct.mif')
dwi_denoise.inputs.out_file = os.path.join(output_dir, 'sub-002_dwi_eddy-correct_dwidenoise.mif')
dwi_denoise.run()



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