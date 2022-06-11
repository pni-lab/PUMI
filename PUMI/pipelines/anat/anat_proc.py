import nipype.interfaces.afni as afni
import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants
from PUMI.engine import NestedNode as Node
from PUMI.pipelines.anat.anat2mni import anat2mni_fsl, anat2mni_ants_hardcoded
from PUMI.pipelines.anat.segmentation import bet_fsl, tissue_segmentation_fsl, bet_hd
from PUMI.engine import AnatPipeline
from PUMI.utils import get_reference


@AnatPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['brain', 'brain_mask', 'head', 'probmap_gm', 'probmap_wm', 'probmap_csf',
                                 'probmap_ventricle', 'parvol_gm', 'parvol_wm', 'parvol_csf', 'partvol_map',
                                 'anat2mni_warpfield', 'mni2anat_warpfield', 'std_brain', 'std_template'])
def anat_proc(wf, bet_tool='FSL', reg_tool='ANTS', **kwargs):
    """

    Performs processing of anatomical images:
    - brain extraction (with either FSL or HD-BET)
    - tissue type segmentation with FSL
    - spatial standardization (with either FSL or ANTS)

    ATTENTION: Images should be already "reoriented" (e.g. with fsl fslreorient2std)

    Parameters
    ----------
    bet_tool (str): Set to brain extraction tool you want to use. Can be 'FSL' or 'HD-BET'
    reg_tool (str): Set to registration tool you want to use. Can be 'FSL' or 'ANTS'

    Inputs
    ----------
    brain (str): Path to the brain which should be segmented.
    stand2anat_xfm (str): Path to standard2input matrix calculated by FSL FLIRT.
                          Only necessary when using prior probability maps!

    Outputs
    ----------
    brain (str): brain extracted image in subject space
    brain_mask (str): brain mask in subject space
    std_brain (str): spatially standardised brain extracted image
    head (str): full head image in subjacet space

    partvol_map (str): hard segmented tissue map
    anat2mni_warpfield (str): spatial standardization warping field

    probmap_csf (str): csf probability map.
    probmap_gm (str): gm probability map.
    probmap_wm (str): wm probability map
    mixeltype (str): mixeltype volume file
    parvol_csf (str): csf partial volume file
    parvol_gm (str): gm partial volume file
    parvol_wm (str): wm partial volume file
    partial_volume_map (str): Path to partial volume map

    Acknowledgements
    ----------
    Adapted from Tamas Spisak (2018) code.

    """

    if bet_tool == 'FSL':
        bet_wf = bet_fsl('bet_fsl')
    elif bet_tool == 'HD-BET':
        bet_wf = bet_hd('hd-bet')
    else:
        raise ValueError('bet_tool can be \'FSL\' or \'HD-BET\' but not ' + bet_tool)

    tissue_segmentation_wf = tissue_segmentation_fsl('tissue_segmentation_fsl')

    if reg_tool == 'FSL':
        anat2mni_wf = anat2mni_fsl('anat2mni_fsl')
    elif reg_tool == 'ANTS':
        anat2mni_wf = anat2mni_ants_hardcoded('anat2mni_ants_hardcoded')
    else:
        raise ValueError('reg_tool can be \'ANTS\' or \'FSL\' but not ' + reg_tool)


    # resample 2mm-std ventricle to the actual standard space
    resample_std_ventricle = Node(interface=afni.Resample(outputtype='NIFTI_GZ',
                                                          in_file=get_reference(wf, 'ventricle_mask')),
                                  name='resample_std_ventricle')

    # transform std ventricle mask to anat space, applying the invers warping filed
    if reg_tool == 'FSL':
        unwarp_ventricle = Node(interface=fsl.ApplyWarp(), name='unwarp_ventricle')
    elif reg_tool == 'ANTS':
        unwarp_ventricle = Node(interface=ants.ApplyTransforms(), name='unwarp_ventricle')

    # mask csf segmentation with anat-space ventricle mask
    ventricle_mask = Node(fsl.ImageMaths(op_string=' -mas'), name="ventricle_mask")

    wf.connect('inputspec', 'in_file', bet_wf, 'in_file')
    wf.connect('inputspec', 'in_file', anat2mni_wf, 'head')

    wf.connect(bet_wf, 'out_file', tissue_segmentation_wf, 'brain')
    wf.connect(bet_wf, 'out_file', anat2mni_wf, 'brain')
    wf.connect(anat2mni_wf, 'inv_linear_xfm', tissue_segmentation_wf, 'stand2anat_xfm')
    wf.connect(anat2mni_wf, 'std_template', resample_std_ventricle, 'master')
    wf.connect(tissue_segmentation_wf, 'probmap_csf', ventricle_mask, 'in_file')

    if reg_tool == 'FSL':
        wf.connect(resample_std_ventricle, 'out_file', unwarp_ventricle, 'in_file')
        wf.connect('inputspec', 'in_file', unwarp_ventricle, 'ref_file')
        wf.connect(anat2mni_wf, 'inv_nonlinear_xfm', unwarp_ventricle, 'field_file')
        wf.connect(anat2mni_wf, 'inv_nonlinear_xfm', 'outputspec', 'mni2anat_warpfield')
        wf.connect(unwarp_ventricle, 'out_file', ventricle_mask, 'in_file2')
    elif reg_tool == 'ANTS':
        wf.connect(resample_std_ventricle, 'out_file', unwarp_ventricle, 'input_image')
        wf.connect('inputspec', 'in_file', unwarp_ventricle, 'reference_image')
        wf.connect(anat2mni_wf, 'inv_nonlinear_xfm', unwarp_ventricle, 'transforms')
        wf.connect(anat2mni_wf, 'inv_nonlinear_xfm', 'outputspec', 'mni2anat_warpfield')
        wf.connect(unwarp_ventricle, 'output_image', ventricle_mask, 'in_file2')

    wf.connect('inputspec', 'in_file', 'outputspec', 'head')
    wf.connect(bet_wf, 'out_file', 'outputspec', 'brain')
    wf.connect(bet_wf, 'brain_mask', 'outputspec', 'brain_mask')
    wf.connect(anat2mni_wf, 'nonlinear_xfm', 'outputspec', 'anat2mni_warpfield')
    wf.connect(anat2mni_wf, 'output_brain', 'outputspec', 'std_brain')
    wf.connect(anat2mni_wf, 'std_template', 'outputspec', 'std_template')
    wf.connect(ventricle_mask, 'out_file', 'outputspec', 'probmap_ventricle')
    wf.connect(tissue_segmentation_wf, 'partial_volume_map', 'outputspec', 'parvol_map')
    wf.connect(tissue_segmentation_wf, 'probmap_csf', 'outputspec', 'probmap_csf')
    wf.connect(tissue_segmentation_wf, 'probmap_gm', 'outputspec', 'probmap_gm')
    wf.connect(tissue_segmentation_wf, 'probmap_wm', 'outputspec', 'probmap_wm')
    wf.connect(tissue_segmentation_wf, 'parvol_csf', 'outputspec', 'parvol_csf')
    wf.connect(tissue_segmentation_wf, 'parvol_gm', 'outputspec', 'parvol_gm')
    wf.connect(tissue_segmentation_wf, 'parvol_wm', 'outputspec', 'parvol_wm')
