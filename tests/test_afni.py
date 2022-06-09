import os
import unittest
from PUMI.engine import BidsPipeline
from PUMI.engine import NestedWorkflow
from PUMI.engine import NestedNode as Node
from nipype.interfaces.fsl import Reorient2Std
from PUMI.pipelines.func.deconfound import despiking_afni

project_root = os.path.dirname(os.path.abspath(__file__))

class TestDespike(unittest.TestCase):

    def test_despike(self):
        @BidsPipeline(output_query=None)
        def despike(wf, **kwargs):
            despike = despiking_afni('despike')
            wf.connect('inputspec', "bold", despike, "in_file")
        wf = despike('despike_test',
                     base_dir=os.path.join(project_root, '../data_out'),
                     bids_dir=os.path.join(project_root, '../data_in/pumi-minitest'))
        self.assertIsInstance(wf, NestedWorkflow)


if __name__ == '__main__':
    unittest.main()
