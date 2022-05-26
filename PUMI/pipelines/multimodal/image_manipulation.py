from nipype import Function

from engine import FuncPipeline

"""
    to extract voxels 10 to 12 inclusive you would specify 10 and 3 (not 10 and 12).
"""


@FuncPipeline(inputspec_fields=['img_4d'],
              outputspec_fields=['img_3d'])
def pick_volume(wf, volume='first', **kwargs):
    """
        Sub-Workflow that extract deals with extracting a 3D-volume choosen by the user from a functional 4D-Sequence

        Parameters
        ----------
        sub_wf : string (nifti file)
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

    '''
        SinkDir = os.path.abspath(os.path.join(sink_dir, sink_tag))
        if not os.path.exists(SinkDir):
            os.makedirs(SinkDir)
    '''

    from nipype.interfaces.fsl import ImageMaths
    from PUMI.engine import Node
    from nipype import Workflow
    import os
    import nipype.pipeline as pe
    import nipype.interfaces.utility as utility
    import nipype.interfaces.fsl as fsl
    import nipype.interfaces.io as io



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



    sub_wf = Workflow('{}'.format(wf))
    if mean:
        sub_wf.connect('inputspec', 'img_4d', img_mean, 'in_file')
        sub_wf.connect(img_mean, 'out_file', 'sinker', 'out_file')
        sub_wf.connect(img_mean, 'out_file', 'outputspec', 'img_3d')
    else:

        sub_wf.connect('inputspec', 'img_4d', img_4d_info, 'in_file')
        sub_wf.connect('inputspec', 'img_4d', fslroi, 'in_file')
        sub_wf.connect(img_4d_info, 'start_idx', fslroi, 't_min')
        sub_wf.connect(fslroi, 'roi_file', 'sinker', 'out_file')
        sub_wf.connect(fslroi, 'roi_file', 'outputspec', 'img_3d')

    return sub_wf



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
    start_idx :
        The index of an Image, from which we start slicing
    """
    from nibabel import load

    # Init variables
    img = load(in_file)
    shape = img.shape
    start_idx = 0

    # Check to make sure the input file is 4-dimensional
    if len(shape) != 4:
        print('Not 4-dim')
        return -1
    # Grab the maximum number of volumes in the 4d-img
    vol_count = img.shape[3]
    # check which volume the user want
    if volume == 'middle':
        print('Middle')
        start_idx = round(vol_count / 2)
    elif volume == 'last':
        print('Last')
        start_idx = vol_count - 1
    # User wants a specific volume
    elif volume.isdigit() and vol_count > int(volume) > 0:
        start_idx = int(volume) - 1
    else :
        raise ValueError('{} is a non-valid value for the Parameter volume \nPossible values : first / middle / last '
                         '/ mean / arbitrary number'.format(volume))

    return int(start_idx)
