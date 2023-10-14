import os
from pathlib import Path
from nipype import Function
from nipype.algorithms import confounds
from nipype.interfaces import afni, fsl, utility
from PUMI.engine import NestedNode as Node, QcPipeline
from PUMI.engine import FuncPipeline
from PUMI.pipelines.multimodal.image_manipulation import pick_volume, timecourse2png
from PUMI.utils import calc_friston_twenty_four, calculate_FD_Jenkinson, mean_from_txt, max_from_txt
from PUMI.plot.carpet_plot import plot_carpet


@QcPipeline(inputspec_fields=['func_1', 'func_2', 'func_corrected'],
              outputspec_fields=['out_file'])
def fieldmap_correction_qc(wf, volume='middle', **kwargs):
    """

    Quality check image generation for fieldmap correction pipeline.

    Inputs:
        func_1 (str): Path to functional image (e.g. LR phase encoded rsfMRI).
        func_2 (str): Path to functional image with another phase encoding than func_1 (e.g. RL phase encoded rsfMRI).
        func_corrected (str): Path to fieldmap corrected functional image.

    Outputs:
        out_file (str): Path to quality check image.

    Sinking:
        - Quality check image.

    """

    def create_montage(vol_1, vol_2, vol_corrected):
        from matplotlib import pyplot as plt
        from pathlib import Path
        from nilearn import plotting
        import os

        fig, axes = plt.subplots(3, 1, facecolor='black', figsize=(10, 15))

        plotting.plot_anat(vol_1, display_mode='ortho', title='Image #1', black_bg=True, axes=axes[0])
        plotting.plot_anat(vol_2, display_mode='ortho', title='Image #2', black_bg=True, axes=axes[1])
        plotting.plot_anat(vol_corrected, display_mode='ortho', title='Corrected', black_bg=True, axes=axes[2])

        path = str(Path(os.getcwd() + '/fieldmap_correction_comparison.png'))
        plt.savefig(path)
        return path

    vol_1 = pick_volume('vol_1', volume=volume)
    wf.connect('inputspec', 'func_1', vol_1, 'in_file')

    vol_2 = pick_volume('vol_2', volume=volume)
    wf.connect('inputspec', 'func_2', vol_2, 'in_file')

    vol_corrected = pick_volume('vol_corrected', volume=volume)
    wf.connect('inputspec', 'func_corrected', vol_corrected, 'in_file')

    montage = Node(Function(
        input_names=['vol_1', 'vol_2', 'vol_corrected'],
        output_names=['out_file'],
        function=create_montage),
        name='montage_node'
    )
    wf.connect(vol_1, 'out_file', montage, 'vol_1')
    wf.connect(vol_2, 'out_file', montage, 'vol_2')
    wf.connect(vol_corrected, 'out_file', montage, 'vol_corrected')

    wf.connect(montage, 'out_file', 'outputspec', 'out_file')
    wf.connect(montage, 'out_file', 'sinker', 'out_file')


@FuncPipeline(inputspec_fields=['func_1', 'func_2'],
              outputspec_fields=['out_file'])
def fieldmap_correction(wf, encoding_direction=['y-', 'y'], readout_times=[0.08264, 0.08264], tr=0.72, **kwargs):
    """

    Fieldmap correction pipeline.

    Parameters:
        encoding_direction (list): List of encoding directions (default is left-right and right-left phase encoding).
        readout_times (list): List of readout times (default adapted to rsfMRI data of the HCP WU 1200 dataset).
        tr (float): Repetition time (default adapted to rsfMRI data of the HCP WU 1200 dataset).

    Inputs:
        func_1 (str): Path to functional image (e.g. LR phase encoded rsfMRI).
        func_2 (str): Path to functional image with another phase encoding than func_1 (e.g. RL phase encoded rsfMRI).

    Outputs:
        out_file (str): 4d distortion corrected image.

    Sinking:
        - 4d distortion corrected image.

    For more information regarding the parameters:
    https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup/ExampleTopupFollowedByApplytopup

    """

    items_to_list_function = lambda item_1, item_2: [item_1, item_2]  # helper function we will need later

    # We use the first volume of func_1 and the first volume of the func_2 4D-image for the estimation of the field.
    first_func1_vol = pick_volume('first_func1_vol', volume='first')
    wf.connect('inputspec', 'func_1', first_func1_vol, 'in_file')

    first_func2_vol = pick_volume('first_func2_vol', volume='first')
    wf.connect('inputspec', 'func_2', first_func2_vol, 'in_file')

    # We need to combine the two 3D images we extracted into one 4D image
    # fsl.Merge expects a list as input, so we need to combine our two 3D images first into a list
    first_volumes_to_list = Node(Function(
        input_names=['item_1', 'item_2'],
        output_names=['output'],
        function=items_to_list_function),
        name='first_volumes_to_list'
    )
    wf.connect(first_func1_vol, 'out_file', first_volumes_to_list, 'item_1')
    wf.connect(first_func2_vol, 'out_file', first_volumes_to_list, 'item_2')

    # Now combine 3D images to 4D image along the time axis
    merger = Node(fsl.Merge(), name='merger')
    merger.inputs.dimension = 't'
    merger.inputs.output_type = 'NIFTI_GZ'
    merger.inputs.tr = tr
    wf.connect(first_volumes_to_list, 'output', merger, 'in_files')

    # Estimate susceptibility induced distortions
    topup = Node(fsl.TOPUP(), name='topup')
    topup.inputs.encoding_direction = encoding_direction
    topup.inputs.readout_times = readout_times
    wf.connect(merger, 'merged_file', topup, 'in_file')

    # The two original 4D files are also needed inside a list
    func_files_to_list = Node(Function(
        input_names=['item_1', 'item_2'],
        output_names=['output'],
        function=items_to_list_function),
        name='func_files_to_list'
    )
    wf.connect('inputspec', 'func_1', func_files_to_list, 'item_1')
    wf.connect('inputspec', 'func_2', func_files_to_list, 'item_2')

    # Apply result of fsl.TOPUP to our original data
    # Result will be one 4D distortion corrected image
    apply_topup = Node(fsl.ApplyTOPUP(), name='apply_topup')
    wf.connect(func_files_to_list, 'output', apply_topup, 'in_files')
    wf.connect(topup, 'out_fieldcoef', apply_topup, 'in_topup_fieldcoef')
    wf.connect(topup, 'out_movpar', apply_topup, 'in_topup_movpar')
    wf.connect(topup, 'out_enc_file', apply_topup, 'encoding_file')

    qc_fieldmap_correction = fieldmap_correction_qc('qc_fieldmap_correction')
    wf.connect('inputspec', 'func_1', qc_fieldmap_correction, 'func_1')
    wf.connect('inputspec', 'func_2', qc_fieldmap_correction, 'func_2')
    wf.connect(topup, 'out_corrected', qc_fieldmap_correction, 'func_corrected')

    wf.connect(apply_topup, 'out_corrected', 'outputspec', 'out_file')
    wf.connect(apply_topup, 'out_corrected', 'sinker', 'out_file')


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
              outputspec_fields=['func_out_file', 'mat_file', 'mc_par_file', 'friston24_file', 'FD_file'])
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

