def onevol_workflow(SinkTag="anat_preproc", wf_name="get_example_vol"):

    """
    This function receives the raw functional image and returns the ROI of the last volume for registration purposes
    as well as information from the header file.

    :param str SinkTag: The output directory in which the returned images could be found.
    :param str wf_name: Name of the workflow.

    **workflow inputs**:

    - func (str) - The functional image.

    **workflow outputs**:

    - func1vol (str) - ROI of last volume.
    - brain-mask (str) - Path to binary brain mask.

    Modified version of Balint Kincses (2018) code.

    """

    import os
    import nipype
    import nipype.pipeline as pe
    import nipype.interfaces.utility as utility
    import nipype.interfaces. fsl as fsl
    import PUMI.func_preproc.info.info_get as info_get
    import nipype.interfaces.io as io
    import PUMI.utils.globals as globals

    SinkDir = os.path.abspath(globals._SinkDir_ + "/" + SinkTag)
    if not os.path.exists(SinkDir):
        os.makedirs(SinkDir)

    # Basic interface class generates identity mappings
    inputspec = pe.Node(utility.IdentityInterface(fields=['func']),
                        name='inputspec')

    # Get dimension infos
    idx = pe.Node(interface=info_get.tMinMax,
                  name='idx')

    # Get the last volume of the func image
    fslroi = pe.Node(fsl.ExtractROI(),
                     name='fslroi')
    fslroi.inputs.t_size = 1

    # Basic interface class generates identity mappings
    outputspec = pe.Node(utility.IdentityInterface(fields=['func1vol']),
                         name='outputspec')

    # Generic datasink module to store structured outputs
    ds = pe.Node(interface=io.DataSink(),
                 name='ds')
    ds.inputs.base_directory = SinkDir
    ds.inputs.regexp_substitutions = [("(\/)[^\/]*$", ".nii.gz")]

    analysisflow = nipype.Workflow(wf_name)
    analysisflow.connect(inputspec, 'func', idx, 'in_files')
    analysisflow.connect(inputspec, 'func', fslroi, 'in_file')
    analysisflow.connect(idx, 'refvolidx', fslroi, 't_min')
    analysisflow.connect(fslroi, 'roi_file', ds, 'funclastvol')
    analysisflow.connect(fslroi, 'roi_file', outputspec, 'func1vol')


    return  analysisflow