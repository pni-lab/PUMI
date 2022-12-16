import unittest
from PUMI.engine import NestedWorkflow
from PUMI.engine import BidsPipeline
import os
from pipelines.rpn_signature import rpn, collect_predictions


# todo rename test_fst to rpn
class TestFsl(unittest.TestCase):

    def test_fsl(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print('Root', project_root)
        input_dir = os.path.join(project_root, 'data_in/pumi-unittest')  # path where the bids data is located

        @BidsPipeline(output_query=None)
        def fsl(wf, **kwargs):
            rpn_wf = rpn(str(wf), bids_dir=input_dir, subjects=['001'])
            collect_predictions(rpn_wf)

        wf = fsl('unittest_fsl',
                 base_dir=os.path.join(project_root, '../data_out'),
                 bids_dir=os.path.join(project_root, '../PUMI/data_in/pumi-unittest'))
        self.assertIsInstance(wf, NestedWorkflow)


if __name__ == '__main__':
    unittest.main()



