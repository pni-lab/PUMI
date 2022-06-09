import unittest
import os
from PUMI.engine import BidsPipeline
from PUMI.engine import NestedWorkflow
from PUMI.engine import NestedNode as Node
from nipype.interfaces.fsl import Reorient2Std
from PUMI.pipelines.func.deconfound import despiking_afni
from PUMI.pipelines.anat.segmentation import bet_fsl, bet_hd
from PUMI.pipelines.anat.anat2mni import anat2mni_fsl, anat2mni_ants, anat2mni_ants_hardcoded

project_root = os.path.dirname(os.path.abspath(__file__))


class TestFsl(unittest.TestCase):

    def test_fsl(self):
        @BidsPipeline(output_query=None)
        def fsl(wf, **kwargs):
            # reorient images
            reorient = Node(interface=Reorient2Std(), name="reorient")
            reorient.inputs.output_type = 'NIFTI_GZ'
            wf.connect('inputspec', "T1w", reorient, 'in_file')

            # Do the brain extraction with FSL
            brain_extraction_fsl = bet_fsl('brain_extraction_fsl')
            wf.connect(reorient, 'out_file', brain_extraction_fsl, 'in_file')

            # transform to MNI with FSL
            anat2mni_fsl_node = anat2mni_fsl('anat2mni_fsl_node', 
                                             ref_head=os.path.join(project_root,
                                                                   '../data_in/std/MNI152_T1_5mm.nii.gz'),
                                             ref_brain=os.path.join(project_root,
                                                                    '../data_in/std/MNI152_T1_5mm_brain.nii.gz'),
                                             ref_brain_mask=os.path.join(project_root,
                                                                         '../data_in/std/MNI152_T1_5mm_brain_mask.nii.gz'))
            wf.connect(brain_extraction_fsl, 'out_file', anat2mni_fsl_node, 'brain')
            wf.connect(reorient, 'out_file', anat2mni_fsl_node, 'head')

        wf = fsl('fsl',
                 base_dir=os.path.join(project_root, '../data_out'),
                 bids_dir=os.path.join(project_root, '../data_in/pumi-minitest'))
        self.assertIsInstance(wf, NestedWorkflow)


if __name__ == '__main__':
    unittest.main()
    