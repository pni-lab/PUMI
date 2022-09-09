from PUMI.engine import AnatPipeline, QcPipeline
from PUMI.engine import NestedNode as Node
from PUMI.utils import get_reference, get_config, create_coregistration_qc, registration_ants_hardcoded
from nipype import Function
from nipype.interfaces import fsl
from nipype.interfaces.ants import Registration, ApplyTransforms
from nipype.interfaces.utility import Function


@QcPipeline(inputspec_fields=['in_file', 'ref_brain'],
            outputspec_fields=['out_file'])
def qc(wf, **kwargs):
    """

    Create quality check images for brain coregistration.

    Inputs:
        in_file (str): Path to the registered brain.

    Ouputs:
        out_file (str): Path to the quality check image

    Sinking:
        - The quality check image

    """
    plot = Node(Function(input_names=['registered_brain', 'template'],
                         output_names=['out_file'],
                         function=create_coregistration_qc),
                name='plot')
    wf.connect('inputspec', 'in_file', plot, 'registered_brain')
    wf.connect('inputspec', 'ref_brain', plot, 'template')

    # sinking
    wf.connect(plot, 'out_file', 'sinker', 'qc_anat2mni')

    # output
    wf.connect(plot, 'out_file', 'outputspec', 'out_file')


@AnatPipeline(inputspec_fields=['brain', 'head'],
              outputspec_fields=['output_brain', 'linear_xfm', 'inv_linear_xfm', 'nonlinear_xfm', 'inv_nonlinear_xfm',
                                 'std_template'])
def anat2mni_fsl(wf,
                 ref_head=None,
                 ref_brain=None,
                 ref_brain_mask=None,
                 **kwargs):
    """

    #Todo Docs

    """


    # Todo: re-think template handling
    if ref_head is None:
        ref_head = get_reference(wf, 'head')
    if ref_brain is None:
        ref_brain = get_reference(wf, 'brain')
    if ref_brain_mask is None:
        ref_brain_mask = get_reference(wf, 'brain_mask')

    # linear registration
    linear_reg = Node(interface=fsl.FLIRT(), name='linear_reg')
    linear_reg.inputs.cost = 'corratio'
    linear_reg.inputs.reference = ref_brain
    wf.connect('inputspec', 'brain', linear_reg, 'in_file')

    # calculate inverse of the flirt transformation matrix
    inv_linear_reg = Node(interface=fsl.utils.ConvertXFM(), name='inv_linear_reg')
    inv_linear_reg.inputs.invert_xfm = True
    wf.connect(linear_reg, 'out_matrix_file', inv_linear_reg, 'in_file')

    # non-linear registration
    nonlinear_reg = Node(interface=fsl.FNIRT(**kwargs), name='nonlinear_reg')
    nonlinear_reg.inputs.ref_file = ref_head
    nonlinear_reg.inputs.refmask_file = ref_brain_mask
    nonlinear_reg.inputs.fieldcoeff_file = True
    nonlinear_reg.inputs.jacobian_file = True
    nonlinear_reg.config_file = get_config(wf, 'FSL', 'fnirt_config')
    wf.connect('inputspec', 'head', nonlinear_reg, 'in_file')
    wf.connect(linear_reg, 'out_matrix_file', nonlinear_reg, 'affine_file')

    # calculate inverse of the fnirt transformation matrix
    inv_nonlinear_reg = Node(interface=fsl.utils.InvWarp(), name="inv_nonlinear_reg")
    wf.connect('inputspec', 'brain', inv_nonlinear_reg, 'reference')
    wf.connect(nonlinear_reg, 'fieldcoeff_file', inv_nonlinear_reg, 'warp')

    # apply the results of FNIRT registration
    brain_warp = Node(interface=fsl.ApplyWarp(), name='brain_warp')
    brain_warp.inputs.ref_file = ref_brain
    wf.connect(nonlinear_reg, 'fieldcoeff_file', brain_warp, 'field_file')
    wf.connect('inputspec', 'brain', brain_warp, 'in_file')

    # QC
    anat2mni_qc = qc(name='anat2mni_fsl_qc', qc_dir=wf.qc_dir)
    wf.connect(brain_warp, 'out_file', anat2mni_qc, 'in_file')
    anat2mni_qc.inputs.inputspec.ref_brain = ref_brain

    # sinking
    wf.connect(brain_warp, 'out_file', 'sinker', 'anat2mni_std')
    wf.connect(nonlinear_reg, 'fieldcoeff_file', 'sinker', 'anat2mni_warpfield')

    # outputs
    wf.get_node('outputspec').inputs.std_template = ref_brain
    wf.connect(linear_reg, 'out_matrix_file', 'outputspec', 'linear_xfm')
    wf.connect(inv_linear_reg, 'out_file', 'outputspec', 'inv_linear_xfm')
    wf.connect(nonlinear_reg, 'fieldcoeff_file', 'outputspec', 'nonlinear_xfm')
    wf.connect(nonlinear_reg, 'field_file', 'outputspec', 'field_file')
    wf.connect(inv_nonlinear_reg, 'inverse_warp', 'outputspec', 'inv_nonlinear_xfm')
    wf.connect(brain_warp, 'out_file', 'outputspec', 'output_brain')


@AnatPipeline(inputspec_fields=['brain', 'head'],
              outputspec_fields=['output_brain', 'xfm', 'inv_xfm', 'std_template'])
def anat2mni_ants(wf,
                  ref_head=None,
                  ref_brain=None,
                  **kwargs):

    """
        Todo docs
    """

    # Todo: re-think template handling
    if ref_head is None:
        ref_head = get_reference(wf, 'head')
    if ref_brain is None:
        ref_brain = get_reference(wf, 'brain')

    reg = Node(interface=Registration(), name="reg")
    reg.inputs.fixed_image = ref_head
    reg.inputs.output_warped_image = True
    # parameters based on: https://gist.github.com/satra/8439778
    reg.inputs.transforms = ['Rigid', 'Affine', 'SyN']
    reg.inputs.transform_parameters = [(0.1,), (0.1,), (0.2, 3.0, 0.0)]
    reg.inputs.number_of_iterations = ([[10000, 111110, 11110]] * 2 + [[100, 50, 30]])
    reg.inputs.dimension = 3
    reg.inputs.write_composite_transform = True
    reg.inputs.collapse_output_transforms = True
    reg.inputs.initial_moving_transform_com = True
    reg.inputs.metric = ['Mattes'] * 2 + [['Mattes', 'CC']]
    reg.inputs.metric_weight = [1] * 2 + [[0.5, 0.5]]
    reg.inputs.radius_or_number_of_bins = [32] * 2 + [[32, 4]]
    reg.inputs.sampling_strategy = ['Regular'] * 2 + [[None, None]]
    reg.inputs.sampling_percentage = [0.3] * 2 + [[None, None]]
    reg.inputs.convergence_threshold = [1.e-8] * 2 + [-0.01]
    reg.inputs.convergence_window_size = [20] * 2 + [5]
    reg.inputs.smoothing_sigmas = [[4, 2, 1]] * 2 + [[1, 0.5, 0]]
    reg.inputs.sigma_units = ['vox'] * 3
    reg.inputs.shrink_factors = [[3, 2, 1]] * 2 + [[4, 2, 1]]
    reg.inputs.use_estimate_learning_rate_once = [True] * 3
    reg.inputs.use_histogram_matching = [False] * 2 + [True]
    reg.inputs.winsorize_lower_quantile = 0.005
    reg.inputs.winsorize_upper_quantile = 0.995
    reg.inputs.args = '--float'
    # ---
    wf.connect('inputspec', 'head', reg, 'moving_image')

    image_transform = Node(interface=ApplyTransforms(), name='image_transform')
    image_transform.inputs.reference_image = ref_brain
    wf.connect('inputspec', 'brain', image_transform, 'input_image')
    wf.connect(reg, 'composite_transform', image_transform, 'transforms')

    # Create png images for quality check
    anat2mni_ants_qc = qc(name='anat2mni_ants_qc', qc_dir=wf.qc_dir)
    anat2mni_ants_qc.inputs.ref_brain = ref_brain
    wf.connect(image_transform, 'output_image', anat2mni_ants_qc, 'in_file')

    # sinking
    wf.connect(reg, 'composite_transform', 'sinker', 'anat2mni_warpfield')
    wf.connect(image_transform, 'output_image', 'sinker', 'warped_brain')

    # outputspec
    wf.get_node('outputspec').inputs.std_template = ref_brain
    wf.connect(reg, 'composite_transform', 'outputspec', 'xfm')
    wf.connect(reg, 'inverse_composite_transform', 'outputspec', 'inv_xfm')
    wf.connect(image_transform, 'output_image', 'outputspec', 'output_brain')


@AnatPipeline(inputspec_fields=['brain', 'head'],
              outputspec_fields=['output_brain', 'linear_xfm', 'inv_linear_xfm', 'nonlinear_xfm', 'inv_nonlinear_xfm',
                                 'std_template'])
def anat2mni_ants_hardcoded(wf,
                            ref_head=None,
                            ref_brain=None,
                            **kwargs
                            ):
    """
        Todo docs
    """
    # Todo: re-think template handling
    if ref_head is None:
        ref_head = get_reference(wf, 'head')
    if ref_brain is None:
        ref_brain = get_reference(wf, 'brain')

    # Calculate linear transformation with FSL (necessary for segmentation with fsl fast if priors are set).
    linear_reg = Node(interface=fsl.FLIRT(), name='linear_reg')
    linear_reg.inputs.cost = 'corratio'
    linear_reg.inputs.reference = ref_brain
    wf.connect('inputspec', 'brain', linear_reg, 'in_file')

    # Calculate the inverse of the linear transformation
    inv_linear_reg = Node(interface=fsl.utils.ConvertXFM(), name='inv_linear_reg')
    inv_linear_reg.inputs.invert_xfm = True
    wf.connect(linear_reg, 'out_matrix_file', inv_linear_reg, 'in_file')

    # Multi-stage registration node with ANTS
    ants_hardcoded = Node(interface=Function(input_names=['brain',
                                                          'reference_brain',
                                                          'head',
                                                          'reference_head'],
                                             output_names=['transform_composite',
                                                           'transform_inverse_composite',
                                                           'warped_image'],
                                             function=registration_ants_hardcoded),
                          name="ants_hardcoded")
    ants_hardcoded.inputs.reference_head = ref_head
    ants_hardcoded.inputs.reference_brain = ref_brain
    wf.connect('inputspec', 'head', ants_hardcoded, 'head')
    wf.connect('inputspec', 'brain', ants_hardcoded, 'brain')

    # Create png images for quality check
    anat2mni_ants_hardcoded_qc = qc(name='anat2mni_ants_hardcoded_qc', qc_dir=wf.qc_dir)
    anat2mni_ants_hardcoded_qc.get_node('inputspec').inputs.ref_brain = ref_brain
    wf.connect(ants_hardcoded, 'warped_image', anat2mni_ants_hardcoded_qc, 'in_file')

    # sinking
    wf.connect(ants_hardcoded, 'warped_image', 'sinker', 'anat2mni')
    wf.connect(ants_hardcoded, 'transform_composite', 'sinker', 'anat2mni_warpfield')

    # outputs
    wf.get_node('outputspec').inputs.std_template = ref_brain
    wf.connect(linear_reg, 'out_matrix_file', 'outputspec', 'linear_xfm')
    wf.connect(inv_linear_reg, 'out_file', 'outputspec', 'inv_linear_xfm')
    wf.connect(ants_hardcoded, 'transform_composite', 'outputspec', 'nonlinear_xfm')
    wf.connect(ants_hardcoded, 'transform_inverse_composite', 'outputspec', 'inv_nonlinear_xfm')
    wf.connect(ants_hardcoded, 'warped_image', 'outputspec', 'output_brain')

