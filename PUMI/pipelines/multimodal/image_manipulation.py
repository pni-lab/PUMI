from PUMI.engine import NestedNode as Node, QcPipeline
from PUMI.engine import FuncPipeline


# To extract voxels 10 to 12 inclusive you would specify 10 and 3 (not 10 and 12).

@FuncPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file'])
def pick_volume(wf, volume='first', **kwargs):
    """
    Sub-Workflow that deals with extracting a 3D-volume choosen by the user from a functional 4D-Sequence

    Parameters:
        wf(str): Name of the workflow.

        volume(str): The volume specified by the user.
            - Possible Values : (first | middle | last | mean | arbitrary number).
            - In case no value was given, the first volume will be returned.
            - In case of a non-valid value, a ValueException will be thrown.

    Returns:
        wf(Workflow): The sub-workflow itself.

    """

    from nipype.interfaces.fsl import ImageMaths
    from PUMI.engine import Node
    import nipype.interfaces.fsl as fsl
    from nipype import Function


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
    Function to get the right index, from which the slicing requested by the user, starts.

    - In case no value was given, the first volume will be returned.

    - In case of a non-valid value, a ValueException will be thrown.

    - Beaware : This function will be called only if the volume != 'mean'

    Parameters:
        in_file(str): Path to input functional run.
        volume(str): The volume specified by the user.
            Possible Values: (first | middle | last | mean | arbitrary number)

    Returns:
        start_idx (integer): The index in the 4d-sequence, from which we start slicing.
    """
    from nibabel import load
    from nipype import Function
    from nipype.interfaces import fsl

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
    start_idx = 0
    if volume == 'first':
        return start_idx
    elif volume == 'middle':
        start_idx = round(vol_count / 2)
    elif volume == 'last':
        start_idx = vol_count - 1
    # User wants a specific volume
    elif volume.isdigit() and vol_count > int(volume) > 0:
        start_idx = int(volume) - 1
    else:
        raise ValueError('{} is a non-valid value for the Parameter volume \nPossible values : first / middle / last '
                         '/ mean / arbitrary number'.format(volume))
    return start_idx


@QcPipeline(inputspec_fields=['bg_image', 'overlay_image'],
            outputspec_fields=['out_file'])
def vol2png(wf, overlay=True, **kwargs):
    """

    # Todo Docs

    """

    from nipype.interfaces import fsl

    slicer = Node(interface=fsl.Slicer(), name='slicer')
    slicer.inputs.image_width = 2000
    slicer.inputs.sample_axial = 5  # set output all axial slices into one picture

    wf.connect('inputspec', 'bg_image', slicer, 'in_file')
    if overlay:
        wf.connect('inputspec', 'overlay_image', slicer, 'image_edges')
    wf.connect(slicer, 'out_file', 'outputspec', 'out_file')


@QcPipeline(inputspec_fields=['func', 'mask', 'x', 'y', 'z'],
            outputspec_fields=['out_file'])
def timecourse2png(wf, plot_type='all', sink=True, **kwargs):
    """
    plot_type: 'all': nothing to specify, will input everything greater than zero
               'vox': use 'x', 'y', 'z' fields for voxel then
               'roi': use 'mask' for roi
    """
    from PUMI.engine import Node
    import nipype.pipeline as pe
    import nipype.interfaces.fsl as fsl
    from nipype import Function


    if plot_type == 'all':
        vox_roi = Node(fsl.ImageMaths(), name='vox_roi')
        def set_inputs(x, y, z):
            return '-roi '\
                           + str(x) + ' 1 '\
                           + str(y) + ' 1 '\
                           + str(z) + ' 1 0 -1 -bin'

        voxroi_args = pe.Node(
            Function(
                input_names=['x', 'y', 'z'],
                output_names=['args'],
                function=set_inputs),
            name="voxroi_args")
    elif plot_type == 'all':
        vox_roi = Node(fsl.ImageMaths(op_string= '-bin'), name='vox_roi')

    mean_ts = Node(fsl.ImageMeants(), name='mean_ts')
    plottimeser = Node(fsl.PlotTimeSeries(), name='plottimeser')

    if plot_type == 'vox':
        wf.connect('inputspec', 'func', vox_roi, 'in_file')
        wf.connect('inputspec', 'x', voxroi_args, 'x')
        wf.connect('inputspec', 'y', voxroi_args, 'y')
        wf.connect('inputspec', 'z', voxroi_args, 'z')
        wf.connect(voxroi_args, 'args', vox_roi, 'args')
        wf.connect(vox_roi, 'out_file', mean_ts, 'mask')
    elif plot_type == 'all':
        wf.connect('inputspec', 'func', vox_roi, 'in_file')
        wf.connect(vox_roi, 'out_file', mean_ts, 'mask')
    elif plot_type == 'roi':
        wf.connect('inputspec', 'mask', mean_ts, 'mask')

    wf.connect('inputspec', 'func',  mean_ts, 'in_file')
    wf.connect(mean_ts, 'out_file', plottimeser, 'in_file')
    wf.connect(plottimeser, 'out_file', 'outputspec', 'out_file')

