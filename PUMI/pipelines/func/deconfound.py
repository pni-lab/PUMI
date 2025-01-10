import os
from pathlib import Path
from nipype import Function
from nipype.algorithms import confounds
from nipype.interfaces import afni, fsl, utility
from PUMI.engine import NestedNode as Node, QcPipeline
from PUMI.engine import FuncPipeline
from PUMI.pipelines.anat.segmentation import bet_deepbet
from PUMI.pipelines.multimodal.image_manipulation import pick_volume, timecourse2png
from PUMI.utils import calc_friston_twenty_four, calculate_FD_Jenkinson, mean_from_txt, max_from_txt, \
    create_segmentation_qc
from PUMI.plot.carpet_plot import plot_carpet


@QcPipeline(inputspec_fields=['background', 'overlay'],
            outputspec_fields=['out_file'])
def qc_fieldmap_correction_fugue(wf, overlay_volume='middle', **kwargs):

    def create_fieldmap_plot(overlay, background):
        from PUMI.utils import plot_roi

        _, output_file = plot_roi(roi_img=overlay, bg_img=background)

        return output_file

    overlay_vol = pick_volume('overlay_vol', overlay_volume)
    wf.connect('inputspec', 'overlay', overlay_vol, 'in_file')

    plot = Node(Function(input_names=['overlay', 'background'],
                         output_names=['out_file'],
                         function=create_fieldmap_plot),
                name='plot')

    wf.connect('inputspec', 'background', plot, 'background')
    wf.connect(overlay_vol, 'out_file', plot, 'overlay')

    wf.connect(plot, 'out_file', 'sinker', 'qc_fieldmap_correction')

    # output
    wf.connect(plot, 'out_file', 'outputspec', 'out_file')


@FuncPipeline(inputspec_fields=['main_img', 'anat_img', 'phasediff_img', 'phasediff_json', 'magnitude_img'],
              outputspec_fields=['out_file'])
def fieldmap_correction_fugue(wf, **kwargs):

    bet_magnitude_img = bet_deepbet('bet_magnitude_img', sinking_name='magnitude_img_segm')
    wf.connect('inputspec', 'magnitude_img', bet_magnitude_img, 'in_file')

    prepare_fieldmap = Node(fsl.PrepareFieldmap(), name='prepare_fieldmap')
    #todo: prepare_fieldmap.inputs.delta_TE = float in ms
    wf.connect(bet_magnitude_img, 'out_file', prepare_fieldmap, 'in_magnitude')
    wf.connect('inputspec', 'phasediff_img', prepare_fieldmap, 'in_phase')

    fugue = Node(fsl.FUGUE(
        dwell_time=0.000324999,    # EffectiveEchoSpacing
        asym_se_time=0.00246
    ), name='fugue')
    wf.connect(prepare_fieldmap, 'out_fieldmap', fugue, 'fmap_in_file')
    wf.connect('inputspec', 'main_img', fugue, 'in_file')

    qc = qc_fieldmap_correction_fugue('qc_fieldmap_correction')
    wf.connect(fugue, 'unwarped_file', qc, 'overlay')
    wf.connect('inputspec', 'anat_img', qc, 'background')

    wf.connect(fugue, 'unwarped_file', 'outputspec', 'out_file')


@FuncPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file'])
def despiking_afni(wf, **kwargs):
    """

    Removes 'spikes' from functional 3d+time images.

    Inputs:
        in_file (str): Path to the 4d image.

    Outputs:
        out_file (str): 4d Image with spikes removed.

    Sinking:
        - The output image

    """
    despike = Node(interface=afni.Despike(**kwargs), name='despike')
    despike.inputs.outputtype = 'NIFTI_GZ'
    wf.connect('inputspec', 'in_file', despike, 'in_file')
    wf.connect(despike, 'out_file', 'outputspec', 'out_file')

    qc_wf = qc('qc_wf')
    wf.connect(despike, 'out_file', qc_wf, 'in_file')


@QcPipeline(inputspec_fields=['in_file'],
            outputspec_fields=['out_file'])
def qc(wf):

    """

    Creates carpet plot after dispiking.

    Inputs:
        in_file (str): Path to dispiked 4d image.

    Outputs:
        out_file (Axes): Matplotlib Axes to be used in composite figures.

    Sinking:
        Carpet plot as png image.

    """

    plot_interface = Function(
        input_names=['img', 'save_carpet'],
        output_names=['ax1'],
        function=plot_carpet)


    # Important because the default of save_carpet is False
    plot_interface.inputs.save_carpet = True

    carpet_node = Node(name='carpet_node',
                       interface=plot_interface)


    wf.connect('inputspec', 'in_file', carpet_node, 'img')

    wf.connect(carpet_node, 'ax1', 'outputspec', 'out_file')


@QcPipeline(inputspec_fields=['func', 'motion_correction', 'plot_motion_trans', 'FD_figure'],
            outputspec_fields=[],
            default_regexp_sub=False,
            regexp_sub=[(r'(.*\/)([^\/]+)\/([^\/]+)\/([^\/]+)$', r'\g<1>qc_motion_correction/\g<3>-\g<2>.png'),
                        ('_subject_', 'sub-')])
def qc_motion_correction_mcflirt(wf, **kwargs):
    """

    Save quality check images for mcflirt motion-correction

    Inputs:
        func (str):
        motion_correction (str):
        plot_motion_trans (str):
        FD_figure (str):



    Sinking:
        - rotations plot
        - translations plot
        - FD plot
        - timeseries

    """

    mc_timecourse = timecourse2png('mc_timeseries', sink=False)  # sink=False important for qc-folder-struktur
    wf.connect('inputspec', 'func', mc_timecourse, 'func')

    # sinking
    wf.connect(mc_timecourse, 'out_file', 'sinker', 'mc_timeseries')
    wf.connect('inputspec', 'motion_correction', 'sinker', 'mc_rotations')
    wf.connect('inputspec', 'plot_motion_trans', 'sinker', 'mc_translations')
    wf.connect('inputspec', 'FD_figure', 'sinker', 'FD')


@FuncPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['func_out_file', 'mat_file', 'mc_par_file', 'friston24_file', 'FD_file',
                                 'mc_ref_vol'])
def motion_correction_mcflirt(wf, reference_vol='middle', FD_mode='Power', **kwargs):
    """

    Use FSL MCFLIRT to do the motion correction of the 4D functional data and use the 6df rigid body motion parameters
    to calculate friston24 parameters for later nuissance regression step.

    Parameters:
        reference_vol (str): Either "first", "middle", "last", "mean", or the index of the volume which the rigid body
         registration (motion correction) will use as reference.
         Default is 'middle'.
        FD_mode: Either "Power" or "Jenkinson"

    Inputs:
        in_file (str): Reoriented functional file

    Outputs:
        func_out_file (str): Path to motion-corrected timeseries
        mat_file (str): Path to motion-correction transformation matrices
        mc_par_file (str): Path to file with motion parameters
        mc_ref_vol (str): Reference volume used for motion correction.
        friston24_file (str): Path to file with friston24 parameters
        FD_file (str): Path to file with FD

    Sinking:
        - motion-corrected timeseries
        - motion-correction transformation matrices
        - absolute and relative displacement parameters
        - friston24 parameters
        - FD
        - FDmax
        - quality check images (FD/rotations/translations and timeseries plot)

    Acknowledgements:
        Adapted from Balint Kincses (2018)

        Modified version of PAC.func_preproc.func_preproc
        (https://github.com/FCP-INDI/C-PAC/blob/main/CPAC/func_preproc/func_preproc.py)
        and CPAC.generate_motion_statistics.generate_motion_statistics
        (https://github.com/FCP-INDI/C-PAC/blob/main/CPAC/generate_motion_statistics/generate_motion_statistics.py)
    """

    if FD_mode not in ['Power', 'Jenkinson']:
        raise ValueError(f'FD_mode has to be "Power" or "Jenkinson"! %s is not a valid option!' % FD_mode)

    refvol = pick_volume(volume=reference_vol, name='refvol')
    wf.connect('inputspec', 'in_file', refvol, 'in_file')

    mcflirt = Node(interface=fsl.MCFLIRT(interpolation="spline", stats_imgs=False), name='mcflirt')
    if reference_vol == "mean":
        mcflirt.inputs.mean_vol = True
    mcflirt.inputs.dof = 6
    mcflirt.inputs.save_mats = True
    mcflirt.inputs.save_plots = True
    mcflirt.inputs.save_rms = True
    mcflirt.inputs.stats_imgs = False
    wf.connect('inputspec', 'in_file', mcflirt, 'in_file')
    if reference_vol != "mean":
        wf.connect(refvol, 'out_file', mcflirt, 'ref_file')

    calc_friston = Node(
        utility.Function(
            input_names=['in_file'], output_names=['out_file'],
            function=calc_friston_twenty_four
        ),
        name='calc_friston'
    )
    wf.connect(mcflirt, 'par_file', calc_friston, 'in_file')

    if FD_mode == "Power":
        calculate_FD = Node(
            confounds.FramewiseDisplacement(
                parameter_source='FSL',
                save_plot=True,
                out_figure='fd_power_2012.png'
            ),
            name='calculate_FD_Power'
        )
    elif FD_mode == "Jenkinson":
        calculate_FD = Node(
            utility.Function(
                input_names=['in_file'],
                output_names=['out_file'],
                function=calculate_FD_Jenkinson
            ),
            name='calculate_FD_Jenkinson'
        )
    wf.connect(mcflirt, 'par_file', calculate_FD, 'in_file')

    mean_FD = Node(
        utility.Function(
            input_names=['in_file', 'axis', 'header', 'out_file'],
            output_names=['mean_file'],
            function=mean_from_txt
        ),
        name='meanFD'
    )
    mean_FD.inputs.axis = 0  # global mean
    mean_FD.inputs.header = True  # global mean
    mean_FD.inputs.out_file = 'FD.txt'
    wf.connect(calculate_FD, 'out_file', mean_FD, 'in_file')

    max_FD = Node(
        utility.Function(
            input_names=['in_file', 'axis', 'header', 'out_file'],
            output_names=['max_file'],
            function=max_from_txt
        ),
        name='maxFD'
    )
    max_FD.inputs.axis = 0  # global mean
    max_FD.inputs.header = True
    max_FD.inputs.out_file = 'FDmax.txt'
    wf.connect(calculate_FD, 'out_file', max_FD, 'in_file')

    plot_motion_rot = Node(
        interface=fsl.PlotMotionParams(in_source='fsl'),
        name='plot_motion_rot')
    plot_motion_rot.inputs.plot_type = 'rotations'
    wf.connect(mcflirt, 'par_file', plot_motion_rot, 'in_file')

    plot_motion_trans = Node(
        interface=fsl.PlotMotionParams(in_source='fsl'),
        name='plot_motion_trans')
    plot_motion_trans.inputs.plot_type = 'translations'
    wf.connect(mcflirt, 'par_file', plot_motion_trans, 'in_file')

    qc_mc = qc_motion_correction_mcflirt('qc_mc')
    wf.connect(plot_motion_rot, 'out_file', qc_mc, 'motion_correction')
    wf.connect(plot_motion_trans, 'out_file', qc_mc, 'plot_motion_trans')
    wf.connect(calculate_FD, 'out_figure', qc_mc, 'FD_figure')
    wf.connect(mcflirt, 'out_file', qc_mc, 'func')

    # sinking
    wf.connect(mcflirt, 'out_file', 'sinker', 'mc_func')
    wf.connect(mcflirt, 'par_file', 'sinker', 'mc_par')
    wf.connect(mcflirt, 'rms_files', 'sinker', 'mc_rms')
    wf.connect(calc_friston, 'out_file', 'sinker', 'mc_first24')
    wf.connect(mean_FD, 'mean_file', 'sinker', 'FD')
    wf.connect(max_FD, 'max_file', 'sinker', 'FDmax')

    # output
    wf.connect(mcflirt, 'out_file', 'outputspec', 'func_out_file')
    wf.connect(mcflirt, 'mat_file', 'outputspec', 'mat_file')
    wf.connect(mcflirt, 'par_file', 'outputspec', 'mc_par_file')
    wf.connect(calculate_FD, 'out_file', 'outputspec', 'FD_file')
    wf.connect(calc_friston, 'out_file', 'outputspec', 'friston24_file')
    wf.connect(refvol, 'out_file', 'outputspec', 'mc_ref_vol')


@QcPipeline(inputspec_fields=['in_file'],
            outputspec_fields=['out_file'])
def qc_nuisance_removal(wf, **kwargs):
    """

    Create quality check images for nuisance removal.

    Inputs:
        in_file (str): Filtered data

    Outputs:
        out_file (str): Path to quality check image

    Sinking:
        - The quality check image

    """

    nuisance_removal_qc = timecourse2png('nuisance_removal_qc')
    wf.connect('inputspec', 'in_file', nuisance_removal_qc, 'func')

    # outputspec
    wf.connect(nuisance_removal_qc, 'out_file', 'outputspec', 'out_file')

    # sinking
    wf.connect(nuisance_removal_qc, 'out_file', 'sinker', 'qc_nuisance_removal')


@FuncPipeline(inputspec_fields=['in_file', 'design_file'],
              outputspec_fields=['out_file'])
def nuisance_removal(wf, **kwargs):
    """

    Perform nuisance removal.

    CAUTION: Name in the old PUMI was nuissremov_workflow

    Parameters:

    Inputs:
        in_file (str): Path to reoriented motion corrected functional data.
        design_file (str): Path to matrix which contains all the nuissance regressors (motion + compcor noise + ...).

    Outputs:
        - Path to the filtered data

    Sinking:
        - Filtered data

    Acknowledgements:
        Adapted from Balint Kincses (2018)

    """
    import nipype.interfaces.fsl as fsl

    nuisance_regression = Node(interface=fsl.FilterRegressor(filter_all=True), name='nuisance_regression')
    wf.connect('inputspec', 'in_file', nuisance_regression, 'in_file')
    wf.connect('inputspec', 'design_file', nuisance_regression, 'design_file')

    # qc
    qc = qc_nuisance_removal('qc')
    wf.connect(nuisance_regression, 'out_file', qc, 'in_file')

    # sinking
    wf.connect(nuisance_regression, 'out_file', 'sinker', 'func_nuis_corrected')

    # output
    wf.connect(nuisance_regression, 'out_file', 'outputspec', 'out_file')

    # TODO: test nuisance removal wf

