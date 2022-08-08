from PUMI.engine import FuncPipeline, Node


@FuncPipeline(inputspec_fields=['wm_mask', 'ventricle_mask'],
              outputspec_fields=['out_file'])
def anat_noise_roi(wf, **kwargs):
    """

    Creates an anatomical noise ROI for use with compcor
    inputs are awaited from the (BBR-based) func2anat registration
    and are already transformed to functional space


    CAUTION: Name in the old PUMI was create_anat_noise_roi_workflow

    Parameters
    ----------

    Inputs
    ----------
    wm_mask (str): Path to white matter mask
    ventricle_mask (str): Path to ventricle mask

    Outputs
    ----------
    out_file (str): path to noise ROI

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
