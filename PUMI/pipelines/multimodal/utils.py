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

    # Get the last volume of the func image
    fslroi = Node(fsl.ExtractROI(), name='fslroi')
    fslroi.inputs.t_size = 1
    wf.connect('inputspec', 'in_file', fslroi, 'in_file')
    wf.connect(idx, 'refvolidx', fslroi, 't_min')
    wf.connect(fslroi, 'roi_file', 'outputspec', 'out_file')