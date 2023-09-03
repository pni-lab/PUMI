from PUMI.engine import FuncPipeline, NestedNode as Node
from nipype.interfaces import fsl, afni
from PUMI.pipelines.anat.segmentation import bet_fsl, bet_hd, bet_deepbet
from PUMI.pipelines.func.compcor import compcor
from PUMI.pipelines.func.concat import concat
from PUMI.pipelines.func.data_censorer import datacens_workflow_threshold
from PUMI.pipelines.func.deconfound import motion_correction_mcflirt, nuisance_removal
from PUMI.pipelines.func.temporal_filtering import temporal_filtering


@FuncPipeline(inputspec_fields=['func', 'cc_noise_roi'],
              outputspec_fields=['func_preprocessed', 'func_preprocessed_scrubbed', 'FD'])
def func_proc_despike_afni(wf, bet_tool='FSL', stdrefvol='middle', fwhm=0, carpet_plot='', **kwargs):

    """

    Perform processing of functional (resting-state) images.

    Parameters:
        bet_tool (str): Set to brain extraction tool you want to use. Can be 'FSL' or 'deepbet'.
        stdrefvol (str): Reference volume (e.g., 'first', 'middle', 'last').
        fwhm (str): Full Width at Half Maximum (FWHM) value.
        carpet_plot (bool): Set to True to generate carpet plots.

    Inputs:
        func (str): Path to reoriented functional image.
        cc_noise_roi (str): Path to noise ROI.

    Outputs:
        func_preprocessed (str): Path to preprocessed functional image.
        func_preprocessed_scrubbed (str): Path to scrubbed preprocessed functional image.
        FD (str): Path to the file containing frame-wise displacement.

    Adapted from Tamas Spisak (2018).

    """

    # ToDo: Add fmri2QC
    # ToDo: Allow HD-Bet

    if bet_tool == 'FSL':
        bet_wf = bet_fsl('bet_fsl', fmri=True)
    elif bet_tool == 'deepbet':
        bet_wf = bet_deepbet('deepbet', fmri=True)
    else:
        raise ValueError('bet_tool can be \'FSL\' or \'deepbet\' but not ' + bet_tool)

    wf.connect('inputspec', 'func', bet_wf, 'in_file')

    motion_correction_mcflirt_wf = motion_correction_mcflirt('motion_correction_mcflirt_wf',
                                                             reference_vol=stdrefvol)
    wf.connect(bet_wf, 'out_file', motion_correction_mcflirt_wf, 'in_file')

    if carpet_plot:
        add_masks = Node(fsl.ImageMaths(op_string=' -add'), name="addimgs")
        wf.connect('inputspec', 'cc_noise_roi', add_masks, 'in_file')
        wf.connect(bet_wf, 'brain_mask', add_masks, 'in_file2')

    despike_wf = Node(afni.Despike(outputtype="NIFTI_GZ"), name="despike_wf")
    wf.connect(motion_correction_mcflirt_wf, 'func_out_file', despike_wf, 'in_file')

    compcor_wf = compcor('compcor_wf') # to  WM+CSF signal
    wf.connect(despike_wf, 'out_file', compcor_wf, 'func_aligned')
    wf.connect('inputspec', 'cc_noise_roi', compcor_wf, 'mask_file')

    concat_wf = concat('concat_wf')
    wf.connect(compcor_wf, 'out_file', concat_wf, 'par1')
    wf.connect(motion_correction_mcflirt_wf, 'friston24_file', concat_wf, 'par2')

    nuisance_removal_wf = nuisance_removal('nuisance_removal_wf') # regress out 5 compcor variables and the Friston24
    wf.connect(concat_wf, 'concat_file', nuisance_removal_wf, 'design_file')
    wf.connect(despike_wf, 'out_file', nuisance_removal_wf, 'in_file')

    # optional smoother:
    if fwhm > 0:
        smoother = Node(interface=fsl.Smooth(fwhm=fwhm), name="smoother")
        wf.connect(nuisance_removal_wf, 'out_file', smoother, 'in_file')

    temportal_filtering_wf = temporal_filtering('temportal_filtering_wf')
    temportal_filtering_wf.get_node('inputspec').inputs.highpass = 0.008
    temportal_filtering_wf.get_node('inputspec').inputs.lowpass = 0.08
    if fwhm > 0:
        wf.connect(smoother, 'smoothed_file', temportal_filtering_wf, 'func')
    else:
        wf.connect(nuisance_removal_wf, 'out_file', temportal_filtering_wf, 'func')

    datacens_workflow_threshold_wf = datacens_workflow_threshold('datacens_workflow_threshold_wf',
                                                                 ex_before=0,
                                                                 ex_after=0)
    wf.connect(motion_correction_mcflirt_wf, 'FD_file', datacens_workflow_threshold_wf, 'FD')
    wf.connect(temportal_filtering_wf, 'out_file', datacens_workflow_threshold_wf, 'func')

    # sinking
    wf.connect(motion_correction_mcflirt_wf, 'FD_file', 'sinker', 'FD')
  
    # output
    wf.connect(motion_correction_mcflirt_wf, 'FD_file', 'outputspec', 'FD')
    wf.connect(datacens_workflow_threshold_wf, 'scrubbed_image', 'outputspec', 'func_preprocessed_scrubbed')
    wf.connect(temportal_filtering_wf, 'out_file', 'outputspec', 'func_preprocessed')

