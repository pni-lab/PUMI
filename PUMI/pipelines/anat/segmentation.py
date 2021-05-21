from ...engine import PumiPipeline
from ...engine import NestedNode as Node
from ...engine import NestedMapNode as MapNode
from ..multimodal.utils import get_vol
from nipype.interfaces import fsl
from nipype.interfaces import io

from PUMI import engine, utils, defaults


@PumiPipeline(inputspec_fields=['background', 'overlay'], outputspec_fields=['qc_image'])
def qc(wf, sink_dir, qc_dir):

    ex_vol_background = get_vol(name="ex_vol_background")
    wf.connect('inputspec', 'background', ex_vol_background, 'in_file')

    ex_vol_overlay = get_vol(name="ex_vol_overlay")
    wf.connect('inputspec', 'overlay', ex_vol_overlay, 'in_file')

    slicer = Node(interface=fsl.Slicer(), name='slicer')
    wf.connect(ex_vol_background, 'out_file', slicer, 'in_file')
    wf.connect(ex_vol_overlay, 'out_file', slicer, 'image_edges')

    slicer.inputs.image_width = 2000
    slicer.inputs.out_file = wf.name
    # set output all axial slices into one picture
    slicer.inputs.sample_axial = 5

    # Sink QC image
    ds_qc = Node(interface=io.DataSink(parameterization=True),
                 name='ds_qc')
    ds_qc.inputs.base_directory = qc_dir
    ds_qc.inputs.regexp_substitutions = [(r"(.*\/)([^\/]+)\/([^\/]+)\/([^\/]+)$", r"\g<1>\g<4>/\g<3>.png"),
                                         ('_subject_', 'sub-')]
    wf.connect(slicer, 'out_file', ds_qc, 'bet')

    wf.connect(slicer, 'out_file', 'outputspec', 'qc_image')


@PumiPipeline(inputspec_fields=['in_file', 'opt_R', 'fract_int_thr', 'vertical_gradient'],
              outputspec_fields=['brain', 'brain_mask'])
def bet_fsl(wf, sink_dir, qc_dir, **kwargs):

    #bet
    bet = Node(interface=fsl.BET(), name='bet')
    bet.inputs.mask = True
    wf.connect('inputspec', 'in_file', bet, 'in_file')

    #qc
    qc_bet = qc(name='qc_bet', qc_dir=qc_dir)
    wf.connect('inputspec', 'in_file', qc_bet, 'background')
    wf.connect(bet, 'out_file', qc_bet, 'overlay')

    # todo: make a cebntral sink node that does all
    #sink
    ds_bet = Node(interface=io.DataSink(), name='ds_bet')
    ds_bet.inputs.base_directory = sink_dir
    ds_bet.inputs.regexp_substitutions = [(r"(.*\/)([^\/]+)\/([^\/]+)\/([^\/]+)$", r"\g<1>\g<3>/\g<4>"),
                                         ('_subject_', 'sub-')]
    wf.connect(bet, 'out_file', ds_bet, 'out_file')
    wf.connect(bet, 'mask_file', ds_bet, 'mask_file')

    # return
    wf.connect(bet, 'out_file', 'outputspec', 'out_file')
    wf.connect(bet, 'mask_file', 'outputspec', 'mask_file')
