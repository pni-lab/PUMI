"""
    to extract voxels 10 to 12 inclusive you would specify 10 and 3 (not 10 and 12).
"""
import os

from nipype.interfaces.fsl import ImageMaths, ExtractROI

from PUMI.engine import Node
from nipype import IdentityInterface, Function, Workflow

'''
    Sub-Workflow that extract deals with extracting a 3D-slice choosen by the user from a functional 4D-Sequence  
    
    Parameters
    ----------
    wf_name : string (nifti file)
       Path to input functional run
    sink_tag :
        Name of the Folder, where sinked data will be stored.
    volume : string
        The slice specified by the user
        Possible Values : (first / middle / last / mean / arbitrary number)
    Returns
    -------
    The sub-workflow it self

'''


def img_extraction_workflow(wf_name='img_wf', sink_tag='Sinked_Data', volume='first'):
    """
        Sub-Workflow that extract deals with extracting a 3D-slice choosen by the user from a functional 4D-Sequence

        Parameters
        ----------
        wf_name : string (nifti file)
           Name of the workflow.
        sink_tag :
            Name of the Folder, where sinked data will be stored.
        volume : string
            The slice specified by the user.
            Possible Values : (first / middle / last / mean / arbitrary number)
            In case of a non-valid value, the first slice will be returned.
        Returns
        --------
        wf_name:
            The sub-workflow itself.
    """

    import os
    import nipype.pipeline as pe
    import nipype.interfaces.utility as utility
    import nipype.interfaces.fsl as fsl
    import definitions
    import nipype.interfaces.io as io

    SinkDir = os.path.abspath(definitions.DATA_OUT_DIR + "/" + sink_tag)
    if not os.path.exists(SinkDir):
        os.makedirs(SinkDir)

    # Basic interface class generates identity mappings
    inputspec = pe.Node(utility.IdentityInterface(fields=['func']),
                        name='inputspec')

    img_4d_info = Node(interface=getImgInfo,
                       name='img_4d_info')
    img_4d_info.inputs.volume = volume

    mean = False
    fslroi = None
    img_mean = None
    if volume == 'mean':
        img_mean = Node(ImageMaths(), op_string='-fmean', name='img_mean_node', out_file='foo_maths.nii')
        print(img_mean.outputs)
        mean = True
    else:
        fslroi = Node(fsl.ExtractROI(),
                      name='fslroi')
        fslroi.inputs.t_size = 1

    # Basic interface class generates identity mappings
    outputspec = pe.Node(utility.IdentityInterface(fields=['func_slice']),
                         name='outputspec')

    # Generic datasink module to store structured outputs
    ds = pe.Node(interface=io.DataSink(),
                 name='ds')
    ds.inputs.base_directory = SinkDir
    ds.inputs.regexp_substitutions = [("(\/)[^\/]*$", ".nii.gz")]

    wf_name = Workflow('{}'.format(wf_name))
    wf_name.connect(inputspec, 'func', img_4d_info, 'in_file')
    if not mean:
        wf_name.connect(inputspec, 'func', fslroi, 'in_file')
        wf_name.connect(img_4d_info, 'start_idx', fslroi, 't_min')
        wf_name.connect(fslroi, 'roi_file', ds, 'in_file')
        wf_name.connect(fslroi, 'roi_file', outputspec, 'func_slice')
    else:
        wf_name.connect(inputspec, 'func', img_mean, 'in_file')
        wf_name.connect(img_mean, 'out_file', ds, 'in_file')
        wf_name.connect(img_mean, 'out_file', outputspec, 'func_slice')

    return wf_name


def get_info(in_file, volume='first'):
    """
    Adapted from C-PAC (https://github.com/FCP-INDI/C-PAC)
    Method to get the right index, from which the slicing requested by the user, occure.
    If the values are not valid, it calculates and returns the very first slice

    Parameters
    ----------
    in_file : string (nifti file)
       Path to input functional run
    volume : string
        The slice specified by the user
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
    start_idx = int(0)

    # Check to make sure the input file is 4-dimensional
    if len(shape) != 4:
        print('Not 4-dim')
        return -1
    # Grab the number of volumes
    vol_count = int(img.shape[3])
    # check which slice the user want

    if volume != 'mean':
        if volume == 'first':
            start_idx = 0
        elif volume == 'middle':
            print('middle')
            print('-------------------------------------------')
            start_idx = round(vol_count / 2)
        elif volume == 'last':
            print('Last')
            print('-------------------------------------------')
            start_idx = vol_count - 1
        # User wants a specific slice
        elif volume.isdigit() and vol_count > int(volume) > 0:
            start_idx = int(volume) - 1
    else:
        return 0
    return start_idx


getImgInfo = Function(input_names=['in_file', 'volume'],
                      output_names=['start_idx', 'volume'],
                      function=get_info)
