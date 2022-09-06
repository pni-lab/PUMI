from PUMI.engine import BidsPipeline
from PUMI.engine import NestedNode as Node
from nipype import Function

# experiment specific parameters:
input_dir = 'data_in/pumi_test_data'  # place where the bids data is located
output_dir = 'data_out'  # place where the folder 'BET' will be created for the results of this script
working_dir = 'data_out'  # place where the folder 'bet_iter_wf' will be created for the workflow


@BidsPipeline(output_query=None)
def load_bids(wf, **kwargs):

    """

     #todo docs

    """

    def printMe(paths):
        print("\n\nanalyzing " + str(paths) + "\n\n")

    analyzeBOLD = Node(Function(function=printMe, input_names=["paths"],
                                output_names=[]), name="analyzeBOLD")

    wf.connect('inputspec', "bold", analyzeBOLD, "paths")


wf = load_bids('load_bids', base_dir='data_out', bids_dir=input_dir)

