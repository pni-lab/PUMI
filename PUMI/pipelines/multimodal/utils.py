from ...engine import QcPipeline
from ...engine import NestedNode as Node
from ...utils import tMinMax
from nipype.interfaces import fsl


@QcPipeline(inputspec_fields=['in_file'],
            outputspec_fields=['out_file'])
def get_vol(wf, idx=0):

    # Get dimension infos
    idx = Node(interface=tMinMax, name='idx')
    wf.connect('inputspec', 'in_file', idx, 'in_files')

    # todo: why  fslroi and not robustfov?
    # Get the last volume of the func image
    fslroi = Node(fsl.ExtractROI(), name='fslroi')
    fslroi.inputs.t_size = 1
    wf.connect('inputspec', 'in_file', fslroi, 'in_file')
    wf.connect(idx, 'refvolidx', fslroi, 't_min')
    wf.connect(fslroi, 'roi_file', 'outputspec', 'out_file')


@QcPipeline(inputspec_fields=['bg_image', 'overlay_image'],
            outputspec_fields=['dummy'])  # todo: handle empty IdentityInterfaces in engine.py
def vol2png(wf, overlay=True, overlayiterated=True):
    myonevol_bg = get_vol(name="onebg")
    wf.connect('inputspec', 'bg_image', myonevol_bg, 'in_file')

    if overlay and not overlayiterated:
        slicer = Node(interface=fsl.Slicer(), name='slicer')

    # Create png images for quality check
    if overlay and overlayiterated:
        myonevol_ol = get_vol(name="oneol")
        wf.connect('inputspec', 'overlay_image', myonevol_ol, 'in_file')
        slicer = Node(interface=fsl.Slicer(), name='slicer')
    if not overlay:
        slicer = Node(interface=fsl.Slicer(), name='slicer')

    slicer.inputs.image_width = 2000
    slicer.inputs.out_file = wf.name
    # set output all axial slices into one picture
    slicer.inputs.sample_axial = 5

    wf.connect(myonevol_bg, 'out_file', slicer, 'in_file')
    if overlay and not overlayiterated:
        wf.connect('inputspec', 'overlay_image', slicer, 'image_edges')
    if overlay and overlayiterated:
        wf.connect(myonevol_ol, 'out_file', slicer, 'image_edges')
    wf.connect(slicer, 'out_file', 'sinker', wf.name)
