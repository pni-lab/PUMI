from PUMI.pipelines.anat.segmentation import bet_fsl
from PUMI._version import get_versions
from configparser import ConfigParser
from PUMI.engine import BidsPipeline
import argparse
import PUMI
import os

cfg_parser = ConfigParser()
cfg_parser.read(os.path.join(os.path.dirname(PUMI.__file__), 'settings.ini'))

__version__ = get_versions()['version']


"""
The following arguments should be in all our BIDS-Apps!
"""
parser = argparse.ArgumentParser(description='BIDS App that does skull stripping with FSL bet.')
parser.add_argument('bids_dir',
                    help='Root directory of the BIDS-compliant input dataset.')
parser.add_argument('output_dir',
                    help='Directory where the results will be stored.')
parser.add_argument('analysis_level',
                    help='Level of the analysis that will be performed.',
                    choices=['participant'])
parser.add_argument('--participant_label',
                    help='Space delimited list of participant-label(s) (e.g. "001 002 003"). '
                         'Perform the tool on the given participants or if this parameter is not '
                         'provided then perform the procedure on all subjects.',
                    default=None,
                    nargs="+")
parser.add_argument('-v', '--version', action='version', version='Version {}'.format(__version__),
                    help='Print version of the application.')
parser.add_argument('--working_dir', type=str, default='.',
                    help='Directory where temporary data will be stored.')

"""
Additionally some more pipeline-specific arguments
"""
parser.add_argument('--frac',
                    default=cfg_parser.getfloat('FSL', 'bet_frac_anat', fallback=0.3),
                    type=float,
                    help='Fractional intensity threshold parameter for FSL BET.')
parser.add_argument('--gradient',
                    default=cfg_parser.getfloat('FSL', 'bet_vertical_gradient', fallback=-0.3),
                    type=float,
                    help='Vertical gradient in fractional intensity threshold for FSL BET.')


args = parser.parse_args()

bids_dir = args.bids_dir
output_dir = args.output_dir
working_dir = args.working_dir
participant_label = args.participant_label


@BidsPipeline(output_query={
    'T1w': dict(
            datatype='anat',
            extension=['nii.gz', 'nii']
    )
})
def bet_wf(wf, **kwargs):
    # Handle pipeline-specific arguments
    wf.cfg_parser['FSL']['bet_frac_anat'] = str(args.frac)  # use wf.cfg_parser and not cfg_parser!!!
    wf.cfg_parser['FSL']['bet_vertical_gradient'] = str(args.gradient)   # use wf.cfg_parser and not cfg_parser!!!
    # ----------------------------------

    bet = bet_fsl('brain_extraction')

    wf.output_dir = os.path.abspath(kwargs.get('output_dir'))
    wf.base_dir = os.path.abspath(kwargs.get('working_dir'))

    wf.connect('inputspec', 'T1w', bet, 'in_file')
    wf.write_graph('bet_wf.png')


bet_func_ex_wf = bet_wf(
    'bet_wf',
    bids_dir=args.bids_dir,
    output_dir=args.output_dir,
    working_dir=working_dir,
    subjects=participant_label
)
