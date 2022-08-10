from nipype import Function
from PUMI.engine import NestedNode as Node, QcPipeline
from nipype.interfaces import fsl
from PUMI.engine import FuncPipeline


"""
    to extract voxels 10 to 12 inclusive you would specify 10 and 3 (not 10 and 12).
"""


@FuncPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file'])
def pick_volume(wf, volume='first', **kwargs):
    """
        Sub-Workflow that deals with extracting a 3D-volume choosen by the user from a functional 4D-Sequence

        Parameters
        ----------
        wf :
           Name of the workflow.
        volume : string
            The volume specified by the user.

            Possible Values : (first / middle / last / mean / arbitrary number)

            In case no value was given, the first volume will be returned.

            In case of a non-valid value, a ValueException will be thrown.
        Returns
        --------
        wf:
            The sub-workflow itself.
    """

    from nipype.interfaces.fsl import ImageMaths
    from PUMI.engine import Node
    import nipype.interfaces.fsl as fsl

    # Basic interface which get the start index, from which the slicing begins
    img_4d_info = Node(Function(input_names=['in_file', 'volume'],
                                output_names=['start_idx'],
                                function=get_info), name='img_4d_info')
    img_4d_info.inputs.volume = volume

    mean = False
    fslroi = None
    img_mean = None
    if volume == 'mean':
        img_mean = Node(ImageMaths(op_string='-Tmean'), name='img_mean_node')
        mean = True
    else:
        fslroi = Node(fsl.ExtractROI(),
                      name='fslroi')
        fslroi.inputs.t_size = 1


    if mean:
        wf.connect('inputspec', 'in_file', img_mean, 'in_file')
        wf.connect(img_mean, 'out_file', 'sinker', 'out_file')
        wf.connect(img_mean, 'out_file', 'outputspec', 'out_file')
    else:
        wf.connect('inputspec', 'in_file', img_4d_info, 'in_file')
        wf.connect('inputspec', 'in_file', fslroi, 'in_file')
        wf.connect(img_4d_info, 'start_idx', fslroi, 't_min')
        wf.connect(fslroi, 'roi_file', 'sinker', 'out_file')
        wf.connect(fslroi, 'roi_file', 'outputspec', 'out_file')




def get_info(in_file, volume='first'):
    """
    Adapted from C-PAC (https://github.com/FCP-INDI/C-PAC)
    Method to get the right index, from which the slicing requested by the user, starts.

    In case no value was given, the first volume will be returned.

    In case of a non-valid value, a ValueException will be thrown.

    Beaware : Will be called only if the volume != 'mean'

    Parameters
    ----------
    in_file : string (nifti file)
       Path to input functional run
    volume : string
        The volume specified by the user
        Possible Values : (first / middle / last / mean / arbitrary number)

    Returns
    -------
        The index in the 4d-sequence, from which we start slicing
    """
    from nibabel import load

    # Init variables
    img = load(in_file)
    shape = img.shape

    # Check to make sure the input file is 4-dimensional
    if len(shape) != 4:
        print('Warning: NOT A 3D VOLUME!')
        return 0
    # Grab the maximum number of volumes in the 4d-img
    vol_count = img.shape[3]
    # check which volume the user want
    if volume == 'first':
        return 0
    elif volume == 'middle':
        return round(vol_count / 2)
    elif volume == 'last':
        return vol_count - 1
    # User wants a specific volume
    elif volume.isdigit() and vol_count > int(volume) > 0:
        return int(volume) - 1
    else:
        raise ValueError('{} is a non-valid value for the Parameter volume \nPossible values : first / middle / last '
                         '/ mean / arbitrary number'.format(volume))


@QcPipeline(inputspec_fields=['bg_image', 'overlay_image'],
            outputspec_fields=['out_file'])
def vol2png(wf, overlay=True, **kwargs):
    slicer = Node(interface=fsl.Slicer(), name='slicer')
    slicer.inputs.image_width = 2000
    slicer.inputs.sample_axial = 5  # set output all axial slices into one picture

    wf.connect('inputspec', 'bg_image', slicer, 'in_file')
    if overlay:
        wf.connect('inputspec', 'overlay_image', slicer, 'image_edges')
    wf.connect(slicer, 'out_file', 'outputspec', 'out_file')

