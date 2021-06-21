from ...engine import QcPipeline, FuncPipeline
from ...engine import NestedNode as Node
from PUMI import utils
from nipype import Function
from nipype.interfaces import fsl


@QcPipeline(inputspec_fields=['in_file'],
            outputspec_fields=['out_file'])
def get_vol(wf, ref_vol='first'):
    # Get dimension infos
    vol_id = get_vol_id(name='vol_id', ref_vol='first')
    wf.connect('inputspec', 'in_file', vol_id, 'in_file')

    # Get the last volume of the func image
    fslroi = Node(fsl.ExtractROI(), name='fslroi')
    # ExtractROI(t_min=4, t_size=-1, ..) would "return" all (-1) scans FROM t=4. This would discard the first 4 scans
    fslroi.inputs.t_size = 1  # get one volume
    wf.connect('inputspec', 'in_file', fslroi, 'in_file')
    wf.connect(vol_id, 'out_file', fslroi, 't_min')
    wf.connect(fslroi, 'roi_file', 'outputspec', 'out_file')


@FuncPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file'])
def get_vol_id(wf, ref_vol='last', **kwargs):
    get_id = Node(Function(input_names=['in_file', 'ref_vol'],
                           output_names=['out_file'],
                           function=utils.vol_id),
                  name='get_id')
    wf.connect('inputspec', 'in_file', get_id, 'in_file')
    get_id.inputs.ref_vol = ref_vol

    wf.connect(get_id, 'out_file', 'outputspec', 'out_file')


@QcPipeline(inputspec_fields=['bg_image', 'overlay_image'],
            outputspec_fields=[])
def vol2png(wf, overlay=True, overlay_iterated=True):
    background_vol = get_vol(name="background_vol")
    wf.connect('inputspec', 'bg_image', background_vol, 'in_file')

    if overlay and overlay_iterated:
        overlay_vol = get_vol(name="overlay_vol")
        wf.connect('inputspec', 'overlay_image', overlay_vol, 'in_file')

    slicer = Node(interface=fsl.Slicer(), name='slicer')
    slicer.inputs.image_width = 2000
    slicer.inputs.out_file = wf.name
    slicer.inputs.sample_axial = 5  # set output all axial slices into one picture
    wf.connect(background_vol, 'out_file', slicer, 'in_file')

    if overlay and overlay_iterated:
        wf.connect(overlay_vol, 'out_file', slicer, 'image_edges')
    if overlay and not overlay_iterated:
        wf.connect('inputspec', 'overlay_image', slicer, 'image_edges')

    wf.connect(slicer, 'out_file', 'sinker', wf.name)
