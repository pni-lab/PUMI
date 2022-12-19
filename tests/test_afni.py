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

            func_proc_wf = func_proc_despike_afni('func_proc_wf')
            wf.connect(reorient_func_wf, 'out_file', func_proc_wf, 'func')
            wf.connect(compcor_roi_wf, 'out_file', func_proc_wf, 'cc_noise_roi')

        wf = despike('unuttest_afni_despike',
                     base_dir=os.path.join(project_root, '../data_out'),
                     bids_dir=os.path.join(project_root, '../data_in/pumi-unittest'))
        self.assertIsInstance(wf, NestedWorkflow)






if __name__ == '__main__':
    unittest.main()
