from ...engine import PumiPipeline
from ...engine import NestedNode as Node
from ...utils import tMinMax
import nipype.interfaces.io as io
from nipype.interfaces import fsl


@PumiPipeline(inputspec_fields=['in_file'], outputspec_fields=['out_file'])
def get_vol(wf, sink_dir, qc_dir, idx=0):

    # Get dimension infos
    idx = Node(interface=tMinMax,
               name='idx')

    # Get the last volume of the func image
    fslroi = Node(fsl.ExtractROI(),
                  name='fslroi')
    fslroi.inputs.t_size = 1

    # Generic datasink module to store structured outputs
    ds = Node(interface=io.DataSink(),
              name='ds')
    ds.inputs.base_directory = sink_dir
    ds.inputs.regexp_substitutions = [("(\/)[^\/]*$", ".nii.gz")] #todo: not here!

    wf.connect('inputspec', 'in_file', idx, 'in_files')
    wf.connect('inputspec', 'in_file', fslroi, 'in_file')
    wf.connect(idx, 'refvolidx', fslroi, 't_min')
    wf.connect(fslroi, 'roi_file', ds, 'funclastvol')

    wf.connect(fslroi, 'roi_file', 'outputspec', 'out_file')