from PUMI.engine import FuncPipeline
from PUMI.engine import NestedNode as Node
import nipype.interfaces.fsl as fsl
import PUMI.pipelines.func.info.info_get as info_get


@FuncPipeline(inputspec_fields=['func'],
              outputspec_fields=['func1vol'],
              regexp_sub=[("(\/)[^\/]*$", ".nii.gz")])
def onevol_workflow(wf, **kwargs):

    """
    This function receives the raw functional image and returns the ROI of the last volume for registration purposes
    as well as information from the header file.

    **workflow inputs**:

    - func (str) - The functional image.

    **workflow outputs**:

    - func1vol (str) - ROI of last volume.
    - brain-mask (str) - Path to binary brain mask.

    Modified version of Balint Kincses (2018) code.

    """

    # Get dimension infos
    idx = Node(interface=info_get.tMinMax, name='idx')
    wf.connect('inputspec', 'func', idx, 'in_files')

    # Get the last volume of the func image
    fslroi = Node(fsl.ExtractROI(), name='fslroi')
    fslroi.inputs.t_size = 1
    wf.connect('inputspec', 'func', fslroi, 'in_file')
    wf.connect(idx, 'refvolidx', fslroi, 't_min')

    # sinking
    wf.connect(fslroi, 'roi_file', 'sinker', 'funclastvol')

    # return
    wf.connect(fslroi, 'roi_file', 'outputspec', 'func1vol')