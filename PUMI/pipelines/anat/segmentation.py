from ...engine import AnatPipeline, QcPipeline
from ...engine import NestedNode as Node
from ...interfaces.HDBet import HDBet
from PUMI.utils import create_segmentation_qc
from nipype import Function
from nipype.interfaces import fsl
from nipype.interfaces.utility import Split
from matplotlib.colors import LinearSegmentedColormap
import os


@QcPipeline(inputspec_fields=['brain', 'head'],
            outputspec_fields=['out_file'])
def qc_bet(wf, **kwargs):
    """

    Create quality check images for brain extraction workflows

    Inputs
    ----------
    brain (str): Path to the extracted brain.
    head (str): Path to the head.

    Ouputs
    ----------
    out_file (str): Path to the quality check image

    Sinking
    ----------
    - The quality check image

    """
    plot = Node(Function(input_names=['overlay', 'bg_img', 'cmap'],
                         output_names=['out_file'],
                         function=create_segmentation_qc),
                name='plot')
    wf.connect('inputspec', 'brain', plot, 'overlay')
    wf.connect('inputspec', 'head', plot, 'bg_img')

    # sinking
    wf.connect(plot, 'out_file', 'sinker', 'qc_bet')

    # output
    wf.connect(plot, 'out_file', 'outputspec', 'out_file')


@QcPipeline(inputspec_fields=['in_file'],
            outputspec_fields=['out_file'])
def qc_tissue_segmentation(wf, **kwargs):
    """

    Create quality check images for tissue segmentation workflows

    Inputs
    ----------
    in_file (str): Path to the partial volume map

    Ouputs
    ----------
    out_file (str): Path to the quality check image

    Sinking
    ----------
    - The quality check image

    """
    plot = Node(Function(input_names=['overlay', 'cmap'],
                         output_names=['out_file'],
                         function=create_segmentation_qc),
                name='plot')
    colors = ['#00A859', '#FFCC29', '#3E4095']
    plot.inputs.cmap = LinearSegmentedColormap.from_list('tissue_segmentation_colors', colors, N=3)
    wf.connect('inputspec', 'in_file', plot, 'overlay')

    # sinking
    wf.connect(plot, 'out_file', 'sinker', 'qc_tissue_segmentation')

    # output
    wf.connect(plot, 'out_file', 'outputspec', 'out_file')


@AnatPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file', 'brain_mask'])
def bet_fsl(wf, **kwargs):

    #bet
    bet = Node(interface=fsl.BET(), name='bet')
    bet.inputs.mask = True
    bet.inputs.robust = True
    bet.inputs.frac = wf.cfg_parser.getfloat('FSL', 'bet_frac', fallback=0.5)
    bet.inputs.vertical_gradient = wf.cfg_parser.getfloat('FSL', 'bet_vertical_gradient', fallback=0)
    wf.connect('inputspec', 'in_file', bet, 'in_file')
    wf.connect(bet, 'out_file', 'sinker', 'out_file')
    wf.connect(bet, 'mask_file', 'sinker', 'mask_file')

    # quality check
    qc = qc_bet(name='qc_bet', qc_dir=wf.qc_dir)
    wf.connect('inputspec', 'in_file', qc, 'head')
    wf.connect(bet, 'out_file', qc, 'brain')

    # return
    wf.connect(bet, 'out_file', 'outputspec', 'out_file')
    wf.connect(bet, 'mask_file', 'outputspec', 'brain_mask')


@AnatPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file', 'brain_mask'])
def bet_hd(wf, **kwargs):
    """
    Does brain extraction with HD-Bet.
    """

    #bet
    bet = Node(interface=HDBet(), name='bet')
    bet.inputs.mode = kwargs.get('mode', wf.cfg_parser.get('HD-Bet', 'mode', fallback='accurate'))
    bet.inputs.device = kwargs.get('device', wf.cfg_parser.get('HD-Bet', 'device', fallback='0'))
    bet.inputs.tta = kwargs.get('tta', wf.cfg_parser.getint('HD-Bet', 'tta', fallback=1))
    bet.inputs.postprocessing = kwargs.get('postprocessing',
                                           wf.cfg_parser.getint('HD-Bet', 'postprocessing', fallback=1))
    bet.inputs.save_mask = kwargs.get('save_mask', wf.cfg_parser.getint('HD-Bet', 'save_mask', fallback=1))
    bet.inputs.overwrite_existing = kwargs.get('overwrite_existing',
                                               wf.cfg_parser.getint('HD-Bet', 'overwrite_existing', fallback=1))
    wf.connect('inputspec', 'in_file', bet, 'in_file')

    # quality check
    qc = qc_bet(name='qc_bet', qc_dir=wf.qc_dir)
    wf.connect('inputspec', 'in_file', qc, 'head')
    wf.connect(bet, 'out_file', qc, 'brain')

    # sinking
    wf.connect(bet, 'out_file', 'sinker', 'out_file')
    wf.connect(bet, 'mask_file', 'sinker', 'mask_file')

    # return
    wf.connect(bet, 'out_file', 'outputspec', 'out_file')
    wf.connect(bet, 'mask_file', 'outputspec', 'brain_mask')


@AnatPipeline(inputspec_fields=['brain', 'stand2anat_xfm'],
              outputspec_fields=['probmap_csf', 'probmap_gm', 'probmap_wm', 'mixeltype', 'parvol_csf', 'parvol_gm',
                                 'parvol_wm', 'partial_volume_map'])
def tissue_segmentation_fsl(wf, priormap=True, **kwargs):
    """

    Perform segmentation of a brain extracted T1w image.

    Parameters
    ----------
    priormap (bool): Set to True if you want to use prior probability maps.
                     In that case the stand2anat_xfm input is needed (otherwise not).

    Inputs
    ----------
    brain (str): Path to the brain which should be segmented.
    stand2anat_xfm (str): Path to standard2input matrix calculated by FSL FLIRT.
                          Only necessary when using prior probability maps!

    Ouputs
    ----------
    probmap_csf (str): Path to csf probability map.
    probmap_gm (str): Path to gm probability map.
    probmap_wm (str): Path to wm probability map
    mixeltype (str): Path to mixeltype volume file
    parvol_csf (str): Path to csf partial volume file
    parvol_gm (str): Path to gm partial volume file
    parvol_wm (str): Path to wm partial volume file
    partial_volume_map (str): Path to partial volume map

    Sinking
    ----------
    - The probability maps for csf, gm and wm.

    Acknowledgements
    ----------
    Modified version of CPAC.seg_preproc.seg_preproc (https://github.com/FCP-INDI/C-PAC) and Balint Kinces code (2018)

    For a deeper insight:
        - https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST
        - https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.fsl.preprocess.html

     """

    if priormap:
        priorprob_csf = os.path.join(os.environ['FSLDIR'], '/data/standard/tissuepriors/avg152T1_csf.hdr')
        priorprob_gm = os.path.join(os.environ['FSLDIR'], '/data/standard/tissuepriors/avg152T1_gray.hdr')
        priorprob_wm = os.path.join(os.environ['FSLDIR'], '/data/standard/tissuepriors/avg152T1_white.hdr')

    fast = Node(interface=fsl.FAST(), name='fast')
    fast.inputs.img_type = 1
    fast.inputs.segments = True
    fast.inputs.probability_maps = True
    fast.inputs.out_basename = 'fast'
    wf.connect('inputspec', 'brain', fast, 'in_files')
    if priormap:
        wf.connect('inputspec', 'stand2anat_xfm', fast, 'init_transform')

    split_probability_maps = Node(interface=Split(), name='split_probability_maps')
    split_probability_maps.inputs.splits = [1, 1, 1]
    split_probability_maps.inputs.squeeze = True
    wf.connect(fast, 'probability_maps', split_probability_maps, 'inlist')

    split_partial_volume_files = Node(interface=Split(), name='split_partial_volume_files')
    split_partial_volume_files.inputs.splits = [1, 1, 1]
    split_partial_volume_files.inputs.squeeze = True
    wf.connect(fast, 'partial_volume_files', split_partial_volume_files, 'inlist')

    qc = qc_tissue_segmentation(name='qc', qc_dir=wf.qc_dir)
    wf.connect(fast, 'partial_volume_map', qc, 'in_file')

    # sinking
    wf.connect(split_probability_maps, 'out1', 'sinker', 'fast_csf')
    wf.connect(split_probability_maps, 'out2', 'sinker', 'fast_gm')
    wf.connect(split_probability_maps, 'out3', 'sinker', 'fast_wm')

    # output
    wf.get_node('outputspec').inputs.probmap_csf = priorprob_csf
    wf.get_node('outputspec').inputs.probmap_gm = priorprob_gm
    wf.get_node('outputspec').inputs.probmap_wm = priorprob_wm
    wf.connect(fast, 'mixeltype', 'outputspec', 'mixeltype')
    wf.connect(fast, 'partial_volume_map', 'outputspec', 'partial_volume_map')
    wf.connect(split_probability_maps, 'out1', 'outputspec', 'probmap_csf')
    wf.connect(split_probability_maps, 'out2', 'outputspec', 'probmap_gm')
    wf.connect(split_probability_maps, 'out3', 'outputspec', 'probmap_wm')
    wf.connect(split_partial_volume_files, 'out1', 'outputspec', 'parvol_csf')
    wf.connect(split_partial_volume_files, 'out2', 'outputspec', 'parvol_gm')
    wf.connect(split_partial_volume_files, 'out3', 'outputspec', 'parvol_wm')
