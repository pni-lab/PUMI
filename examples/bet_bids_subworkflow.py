import argparse
from PUMI.engine import BidsPipeline
from PUMI.pipelines.anat.segmentation import bet_hd
import os


if __name__ == '__main__':
    ROOT_DIR = os.path.dirname(os.getcwd())
    input_dir = os.path.join(ROOT_DIR, 'data_in/pumi-unittest')  # path where the bids data is located
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
        'T1w': dict(
            datatype='anat',
            extension=['nii', 'nii.gz']
        )
    })
    def bet_wf(wf, **kwargs):
        """

         Example for Brain Extraction workflow

        """

        bet = bet_hd('brain_extraction')

        wf.connect('inputspec', 'T1w', bet, 'in_file')
        wf.write_graph('bet_wf.png')



    bet_ex_wf = bet_wf('bet_func_ex_wf', bids_dir=args.input_dir,
                           output_dir=args.output_dir, subjects=['001'])


