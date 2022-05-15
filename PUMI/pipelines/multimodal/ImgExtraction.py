from nipype import Function

"""
    to extract voxels 10 to 12 inclusive you would specify 10 and 3 (not 10 and 12).
"""


def img_extraction_workflow(wf_name='img_wf', sink_dir='', sink_tag='Sinked_Data', volume='first'):
    """
        Sub-Workflow that extract deals with extracting a 3D-volume choosen by the user from a functional 4D-Sequence

        Parameters
        ----------
        wf_name : string (nifti file)
           Name of the workflow.
        sink_tag :
            Name of the Folder, where sinked data will be stored.
        sink_dir :
            Directory of sinked data
        volume : string
            The volume specified by the user.
            Possible Values : (first / middle / last / mean / arbitrary number)
            In case of a non-valid value, the first volume will be returned.
        Returns
        --------
        wf_name:
            The sub-workflow itself.
    """

    from nipype.interfaces.fsl import ImageMaths
    from PUMI.engine import Node
    from nipype import Workflow
    import os
    import nipype.pipeline as pe
    import nipype.interfaces.utility as utility
    import nipype.interfaces.fsl as fsl
    import nipype.interfaces.io as io

    SinkDir = os.path.abspath(sink_dir + "/" + sink_tag)
    if not os.path.exists(SinkDir):
        os.makedirs(SinkDir)

    # Basic interface class generates identity mappings
    inputspec = pe.Node(utility.IdentityInterface(fields=['func']),
                        name='inputspec')

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

    # Basic interface class generates identity mappings
    outputspec = pe.Node(utility.IdentityInterface(fields=['func_volume']),
                         name='outputspec')

    # Generic datasink module to store structured outputs
    ds = pe.Node(interface=io.DataSink(),
                 name='ds')
    ds.inputs.base_directory = SinkDir
    ds.inputs.regexp_substitutions = [("(\/)[^\/]*$", ".nii.gz")]

    wf_name = Workflow('{}'.format(wf_name))
    if mean:
        wf_name.connect(inputspec, 'func', img_mean, 'in_file')
        wf_name.connect(img_mean, 'out_file', ds, 'in_file')
        wf_name.connect(img_mean, 'out_file', outputspec, 'func_volume')
    else:
        wf_name.connect(inputspec, 'func', img_4d_info, 'in_file')
        wf_name.connect(inputspec, 'func', fslroi, 'in_file')
        wf_name.connect(img_4d_info, 'start_idx', fslroi, 't_min')
        wf_name.connect(fslroi, 'roi_file', ds, 'in_file')
        wf_name.connect(fslroi, 'roi_file', outputspec, 'func_volume')

    return wf_name


def get_info(in_file, volume='first'):
    """
    Adapted from C-PAC (https://github.com/FCP-INDI/C-PAC)
    Method to get the right index, from which the slicing requested by the user, occure.
    If the values are not valid, it calculates and returns the very first volume

    Will be called only if the volume != 'mean'

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

    return int(start_idx)
