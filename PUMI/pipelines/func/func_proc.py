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
        bet_tool (str): Set to brain extraction tool you want to use. Can be 'FSL', 'HD-BET' or 'deepbet'.
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
    # ToDo: check if variable names and node names are the same

    if bet_tool == 'FSL':
        bet_wf = bet_fsl('bet_fsl')
    elif bet_tool == 'HD-BET':
        bet_wf = bet_hd('hd-bet')
    elif bet_tool == 'deepbet':
        bet_wf = bet_deepbet('deepbet')
    else:
        raise ValueError('bet_tool can be \'FSL\', \'HD-BET\' or \'deepbet\' but not ' + bet_tool)

    wf.connect('inputspec', 'func', bet_wf, 'in_file')

    mymc = motion_correction_mcflirt('mymc', reference_vol=stdrefvol)
    wf.connect(bet_wf, 'out_file', mymc, 'in_file')

    if carpet_plot:
        add_masks = Node(fsl.ImageMaths(op_string=' -add'), name="addimgs")
        wf.connect('inputspec', 'cc_noise_roi', add_masks, 'in_file')
        wf.connect(bet_wf, 'brain_mask', add_masks, 'in_file2')

    mydespike = Node(afni.Despike(outputtype="NIFTI_GZ"), name="DeSpike")
    wf.connect(mymc, 'func_out_file', mydespike, 'in_file')

    mycmpcor = compcor('mycmpcor') # to  WM+CSF signal
    wf.connect(mydespike, 'out_file', mycmpcor, 'func_aligned')
    wf.connect('inputspec', 'cc_noise_roi', mycmpcor, 'mask_file')

    myconc = concat('myconc')
    wf.connect(mycmpcor, 'out_file', myconc, 'par1')
    wf.connect(mymc, 'friston24_file', myconc, 'par2')

    mynuisscor = nuisance_removal('mynuisscor') # regress out 5 compcor variables and the Friston24
    wf.connect(myconc, 'concat_file', mynuisscor, 'design_file')
    wf.connect(mydespike, 'out_file', mynuisscor, 'in_file')

    # optional smoother:
    if fwhm > 0:
        smoother = Node(interface=fsl.Smooth(fwhm=fwhm), name="smoother")
        wf.connect(mynuisscor, 'out_file', smoother, 'in_file')

    mytmpfilt = temporal_filtering('mytmpfilt')
    mytmpfilt.get_node('inputspec').inputs.highpass = 0.008
    mytmpfilt.get_node('inputspec').inputs.lowpass = 0.08
    if fwhm > 0:
        wf.connect(smoother, 'smoothed_file', mytmpfilt, 'func')
    else:
        wf.connect(mynuisscor, 'out_file', mytmpfilt, 'func')

    myscrub = datacens_workflow_threshold('myscrub', ex_before=0, ex_after=0)
    wf.connect(mymc, 'FD_file', myscrub, 'FD')
    wf.connect(mytmpfilt, 'out_file', myscrub, 'func')

    # sinking
    wf.connect(mymc, 'FD_file', 'sinker', 'FD')
  
    # output
    wf.connect(mymc, 'FD_file', 'outputspec', 'FD')
    wf.connect(myscrub, 'scrubbed_image', 'outputspec', 'func_preprocessed_scrubbed')
    wf.connect(mytmpfilt, 'out_file', 'outputspec', 'func_preprocessed')

