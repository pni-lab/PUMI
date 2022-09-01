from PUMI.engine import FuncPipeline, NestedNode as Node, QcPipeline
from PUMI.pipelines.multimodal.image_manipulation import vol2png


@FuncPipeline(inputspec_fields=['wm_mask', 'ventricle_mask'],
              outputspec_fields=['out_file'])
def anat_noise_roi(wf, **kwargs):
    """

    Creates an anatomical noise ROI for use with compcor.
    Inputs are awaited from the (BBR-based) func2anat registration and are already transformed to functional space.

    CAUTION: Name in the old PUMI was create_anat_noise_roi_workflow

    Parameters
    ----------

    Inputs
    ----------
    wm_mask (str): Path to white matter mask
    ventricle_mask (str): Path to ventricle mask

    Outputs
    ----------
    out_file (str): Path to noise ROI

    Sinking
    ----------

    Acknowledgements
    ----------
    Adapted from Tamas Spisak (2018)

    """

    import nipype.interfaces.fsl as fsl

    # erode WM mask in functional space
    erode_mask = Node(fsl.ErodeImage(), name="erode_mask")
    wf.connect('inputspec', 'wm_mask', erode_mask, 'in_file')

    # add ventricle and eroded WM masks
    add_masks = Node(fsl.ImageMaths(op_string=' -add'), name="add_masks")
    wf.connect('inputspec', 'ventricle_mask', add_masks, 'in_file')
    wf.connect(erode_mask, 'out_file', add_masks, 'in_file2')

    # output
    wf.connect(add_masks, 'out_file', 'outputspec', 'out_file')


@QcPipeline(inputspec_fields=['func_aligned', 'mask_file'],
            outputspec_fields=[])
def compcor_qc(wf, **kwargs):
    """

    Save quality check images for mcflirt motion-correction

    Inputs
    ----------
    func_aligned (str): Reoriented and realigned functional image
    mask_file (str): Mask files which determine ROI(s)

    Outputs
    ----------

    Sinking
    ----------
    - compcor qc image

    """

    compcor_wf = vol2png("compcor_qc")
    wf.connect('inputspec', 'func_aligned', compcor_wf, 'bg_image')
    wf.connect('inputspec', 'mask_file', compcor_wf, 'overlay_image')
    wf.connect(compcor_wf, 'out_file', 'sinker', 'qc_compcor')


@FuncPipeline(inputspec_fields=['func_aligned', 'mask_file'],
              outputspec_fields=['out_file'])
def compcor(wf, **kwargs):
    """

    Component based noise reduction method (Behzadi et al.,2007): Regressing out principal components from noise ROIs.
    Here the aCompCor is used.

    Inputs
    ----------
    func_aligned (str): Reoriented and realigned functional image
    mask_files (str): Mask files which determine ROI(s)

    Outputs
    ----------
    out_file (str): Path to text file containing the noise components

    Sinking
    ----------
    - Text file containing the noise components
    - Mask files which determine ROI(s)

    Acknowledgements
    ----------
    Adapted from Balint Kincses (2018)

    """

    import nipype.algorithms.confounds as cnf
    import nipype.interfaces.utility as utility
    from PUMI.pipelines.func.info.get_info import get_repetition_time
    from PUMI.utils import scale_vol, drop_first_line

    scale = Node(
        interface=utility.Function(
            input_names=['in_file'],
            output_names=['scaled_file'],
            function=scale_vol
        ),
        name='scale'
    )
    wf.connect('inputspec', 'func_aligned', scale, 'in_file')

    time_repetition = Node(
        interface=utility.Function(
            input_names=['in_file'],
            output_names=['TR'],
            function=get_repetition_time
        ),
        name='time_repetition'
    )
    wf.connect('inputspec', 'func_aligned', time_repetition, 'in_file')

    compcor = Node(
        interface=cnf.ACompCor(
            pre_filter='polynomial',
            header_prefix="",
            num_components=5
        ),
        name='compcor'
    )
    wf.connect(scale, 'scaled_file', compcor, 'realigned_file')
    wf.connect('inputspec', 'mask_file', compcor, 'mask_files')
    wf.connect(time_repetition, 'TR', compcor, 'repetition_time')

    # Drop first line of the Acompcor function output
    drop_first_line = Node(
        interface=utility.Function(
            input_names=['in_file'],
            output_names=['out_file'],
            function=drop_first_line
        ),
        name='drop_first_line'
    )
    wf.connect(compcor, 'components_file', drop_first_line, 'in_file')

    # qc
    qc = compcor_qc('qc')
    wf.connect('inputspec', 'func_aligned', qc, 'func_aligned')
    wf.connect('inputspec', 'mask_file', qc, 'mask_file')

    # output
    wf.connect(drop_first_line, 'out_file', 'outputspec', 'out_file')

    # sinking
    wf.connect(compcor, 'components_file', 'sinker', 'compcor_noise')
    wf.connect('inputspec', 'mask_file', 'sinker', 'compcor_noise_mask')
