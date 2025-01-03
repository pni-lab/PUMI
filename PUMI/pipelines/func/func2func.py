from nipype.interfaces import fsl
from PUMI.engine import AnatPipeline, NestedNode as Node, QcPipeline
from PUMI.pipelines.multimodal.image_manipulation import pick_volume, vol2png


@QcPipeline(inputspec_fields=['registered_func', 'func_2'],
            outputspec_fields=['out_file'])
def qc(wf, registered_func_volume='middle', func_2_volume='middle', **kwargs):
    """
    Creates quality check images for func2func workflow.

    Parameters:
        registered_func_volume: Select which volume from registered image to use as overlay
                            (i.e., 'first', 'middle', 'last', 'mean' or an arbitrary volume).
        func_2_volume: Select which volume from func_2 to use as background.
                            (i.e., 'first', 'middle', 'last', 'mean' or an arbitrary volume).

    Inputs:
        registered_func (str): Path to registered functional image.
        func_2 (str): Path to 4D reference image (e.g., sbref).
    """

    one_registered_func_volume = pick_volume('one_registered_func_volume', volume=registered_func_volume, sink=False)
    wf.connect('inputspec', 'registered_func', one_registered_func_volume, 'in_file')

    one_func_2_volume = pick_volume('one_func_2_volume', volume=func_2_volume, sink=False)
    wf.connect('inputspec', 'registered_func', one_func_2_volume, 'in_file')

    qc_vol2png = vol2png(wf.name + '_vol2png')
    wf.connect(one_registered_func_volume, 'out_file', qc_vol2png, 'overlay_image')
    wf.connect(one_func_2_volume, 'out_file', qc_vol2png, 'bg_image')

    #  Output
    wf.connect(qc_vol2png, 'out_file', 'outputspec', 'out_file')

    # sinking
    wf.connect(qc_vol2png, 'out_file', 'sinker', wf.name)


@AnatPipeline(inputspec_fields=['func_1', 'func_2'],
              outputspec_fields=['out_file', 'func_to_func_2_matrix', 'inv_func_to_func_2_matrix'])
def func2func(wf, func_1_volume='mean', func_2_volume='mean', **kwargs):
    """
    Register one functional image to another functional image.

    Parameters:
        func_1_volume (str): Select which volume from func_1 to use for calculation of transformation matrix
                            (i.e., 'first', 'middle', 'last', 'mean' or an arbitrary volume).
        func_2_volume (str): Select which volume from func_2 to use as reference for calculation of transformation matrix.
                            (i.e., 'first', 'middle', 'last', 'mean' or an arbitrary volume).

    Inputs:
        func_1 (str): Path to 4D functional image (e.g., rsfMRI scan).
        func_2 (str): Path to 4D reference image (e.g., sbref).

    Returns:
        out_file (str): Registered functional image.
        func_to_func_2_matrix: Transformation matrix (func_1 to func_2).
        inv_func_to_func_2_matrix: Inverse transformation matrix (func_2 to func_1).
    """

    # Select volumes from func_1
    func_1_volume_selected = pick_volume('func_1_volume_selected', volume=func_1_volume)
    wf.connect('inputspec', 'func_1', func_1_volume_selected, 'in_file')

    # Select volumes from func_2
    func_2_volume_selected = pick_volume('func_2_volume_selected', volume=func_2_volume)
    wf.connect('inputspec', 'func_2', func_2_volume_selected, 'in_file')

    # Linear registration (FLIRT) to register selected volumes from func_1 and func_2
    linear_func_to_func_2 = Node(interface=fsl.FLIRT(), name='linear_func_to_func_2')
    linear_func_to_func_2.inputs.cost = 'corratio'
    linear_func_to_func_2.inputs.dof = 6
    linear_func_to_func_2.inputs.out_matrix_file = "func_to_func_2.mat"
    wf.connect(func_1_volume_selected, 'out_file', linear_func_to_func_2, 'in_file')
    wf.connect(func_2_volume_selected, 'out_file', linear_func_to_func_2, 'reference')

    # Calculate the inverse of the transformation matrix
    invert_matrix = Node(interface=fsl.utils.ConvertXFM(), name='invert_matrix')
    invert_matrix.inputs.invert_xfm = True
    wf.connect(linear_func_to_func_2, 'out_matrix_file', invert_matrix, 'in_file')

    # Apply transformation matrix to the entire 4D func_1 image
    apply_xfm_4d = Node(interface=fsl.ApplyXFM(), name='apply_xfm_4d')
    apply_xfm_4d.inputs.interp = 'trilinear'
    wf.connect('inputspec', 'func_1', apply_xfm_4d, 'in_file')  # entire 4D func_1 image
    wf.connect(linear_func_to_func_2, 'out_matrix_file', apply_xfm_4d, 'in_matrix_file')
    wf.connect('inputspec', 'func_2', apply_xfm_4d, 'reference')  # entire 4D func_2 image

    # QC
    func2func_qc = qc('func2func_qc')
    wf.connect(apply_xfm_4d, 'out_file', func2func_qc, 'registered_func')
    wf.connect('inputspec', 'func_2', func2func_qc, 'func_2')

    # Sinking
    wf.connect(apply_xfm_4d, 'out_file', 'sinker', 'registered_func')

    # Outputs
    wf.connect(apply_xfm_4d, 'out_file', 'outputspec', 'out_file')
    wf.connect(linear_func_to_func_2, 'out_matrix_file', 'outputspec', 'func_to_func_2_matrix')
    wf.connect(invert_matrix, 'out_file', 'outputspec', 'inv_func_to_func_2_matrix')
