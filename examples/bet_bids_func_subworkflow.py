from PUMI.engine import BidsPipeline
from PUMI.pipelines.anat.segmentation import bet_fsl
import argparse
import os


"""
    Using command line arguments, one can set the paths to the input/output/working directory of the workflow.
    Remember to enter a full path.
    
    If nothing was given, default paths will be used.(Might cause Exception)
"""


ROOT_DIR = os.path.dirname(os.getcwd())
input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
output_dir = os.path.join(ROOT_DIR,
                          'data_out')  # path where the folder 'BET' will be created for the results of this script
working_dir = os.path.join(ROOT_DIR,
                           'data_out')  # path where the folder 'bet_iter_wf' will be created for the workflow

# Create command line parser in case user wanted to specify the paths.
parser = argparse.ArgumentParser(
    description='Using command line arguments, one can optionally set the paths to the '
                'input/output/working directory of the workflow.')
parser.add_argument('-input_dir', nargs='?', metavar='input_dir', type=str, default=input_dir,
                    help='Path to Bids-Directory path')
parser.add_argument('-output_dir', nargs='?', metavar='output_dir', type=str, default=output_dir,
                    help='Path to output directory')
parser.add_argument('-working_dir', nargs='?', metavar='working_dir', type=str, default=working_dir,
                    help='Path, where Workflow Data will '
                         'be stored')
args = parser.parse_args()


@BidsPipeline(output_query={
    'bold': dict(
            datatype='func',
            extension=['nii.gz', 'nii']
        )
})
def bet_wf(wf, **kwargs):

    """

     Example for Brain Extraction workflow

    """

    bet = bet_fsl('brain_extraction', fmri=True)
    wf.output_dir = kwargs.get('output_dir')
    wf.base_dir = os.path.abspath(args.working_dir)


    wf.connect('inputspec', 'bold', bet, 'in_file')
    wf.write_graph('bet_func_ex_wf.png')


print(input_dir)
bet_func_ex_wf = bet_wf('bet_func_ex_wf', bids_dir=args.input_dir,
                        output_dir=args.output_dir, subjects=['001'])
