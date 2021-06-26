from ...engine import AnatPipeline, QcPipeline, PumiPipeline
from ...engine import NestedNode as Node
from ...interfaces.HDBet import HDBet
from ..multimodal.utils import get_vol
from nipype.interfaces import fsl

# from PUMI import engine, utils, defaults


@QcPipeline(inputspec_fields=['background', 'overlay'],
            outputspec_fields=['qc_image'])
def qc(wf):

    ex_vol_background = get_vol(name="ex_vol_background", qc_dir=wf.qc_dir)
    wf.connect('inputspec', 'background', ex_vol_background, 'in_file')

    ex_vol_overlay = get_vol(name="ex_vol_overlay", qc_dir=wf.qc_dir)
    wf.connect('inputspec', 'overlay', ex_vol_overlay, 'in_file')

    slicer = Node(interface=fsl.Slicer(), name='slicer')
    slicer.inputs.image_width = 2000
    slicer.inputs.out_file = wf.name
    # set output all axial slices into one picture
    slicer.inputs.sample_axial = 5
    wf.connect(ex_vol_background, 'out_file', slicer, 'in_file')
    wf.connect(ex_vol_overlay, 'out_file', slicer, 'image_edges')

    # Sink QC image
    wf.connect(slicer, 'out_file', 'sinker', 'bet')

    # return
    wf.connect(slicer, 'out_file', 'outputspec', 'qc_image')


@AnatPipeline(inputspec_fields=['in_file', 'opt_R', 'fract_int_thr', 'vertical_gradient'],
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

    #qc
    qc_bet = qc(name='qc_bet', qc_dir=wf.qc_dir)
    wf.connect('inputspec', 'in_file', qc_bet, 'background')
    wf.connect(bet, 'out_file', qc_bet, 'overlay')

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

    #qc
    qc_bet = qc(name='qc_bet', qc_dir=wf.qc_dir)
    wf.connect('inputspec', 'in_file', qc_bet, 'background')
    wf.connect(bet, 'out_file', qc_bet, 'overlay')

    #sinking
    wf.connect(bet, 'out_file', 'sinker', 'out_file')
    wf.connect(bet, 'mask_file', 'sinker', 'mask_file')

    # return
    wf.connect(bet, 'out_file', 'outputspec', 'out_file')
    wf.connect(bet, 'mask_file', 'outputspec', 'brain_mask')



