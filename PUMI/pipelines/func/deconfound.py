from nipype import Function
from nipype.algorithms import confounds
from nipype.interfaces import afni, fsl, utility
from PUMI.engine import NestedNode as Node, QcPipeline
from PUMI.engine import FuncPipeline
from PUMI.pipelines.anat.segmentation import bet_deepbet
from PUMI.pipelines.multimodal.image_manipulation import pick_volume, timecourse2png
from PUMI.utils import calc_friston_twenty_four, calculate_FD_Jenkinson, mean_from_txt, max_from_txt
from PUMI.plot.carpet_plot import plot_carpet


@QcPipeline(inputspec_fields=['main', 'fmap', 'func_corrected'],
              outputspec_fields=['out_file'])
def qc_fieldmap_correction_topup(wf, volume='first', **kwargs):
    """

    Generate quality control image for the fieldmap correction consisting of a montage image
    comparing a main volume, a fieldmap volume and a volume of the corrected fieldmap.

    Parameters:
        volume (str): The volume of the functional data to be used for comparison (e.g., 'middle').
                      Default is 'first'.

    Inputs:
        main (str): Path to the main sequence functional image (e.g., functional data).
        fmap (str): Path to the fieldmap image (e.g., uncorrected fieldmap data).
        func_corrected (str): Path to the fieldmap-corrected functional image.

    Outputs:
        out_file (str): Path to the saved QC montage image comparing the original and corrected images.

    Sinking:
        - Path to QC comparison image (PNG file showing the original and corrected volumes).

    """

    def create_montage(vol_main, vol_fmap, vol_corrected, n_slices=3):
        from matplotlib import pyplot as plt
        from pathlib import Path
        from nilearn import plotting
        import os

        def get_cut_cords(func, n_slices=3):
            import nibabel as nib
            import numpy as np

            func_img = nib.load(func)
            y_dim = func_img.shape[1]  # y-dimension (coronal direction) is the second dimension in the image shape

            slices = np.linspace(-y_dim / 2, y_dim / 2, n_slices)
            # slices might contain floats but this is not a problem since nilearn will round floats to the
            # nearest integer value!
            return slices

        fig, axes = plt.subplots(3, 1, facecolor='black', figsize=(12, 18))
        plt.subplots_adjust(hspace=0.4)
        plotting.plot_anat(vol_main, display_mode='y', cut_coords=get_cut_cords(vol_main, n_slices=n_slices),
                           title='Image #1', black_bg=True, axes=axes[0])
        plotting.plot_anat(vol_fmap, display_mode='y', cut_coords=get_cut_cords(vol_fmap, n_slices=n_slices),
                           title='Image #2', black_bg=True, axes=axes[1])
        plotting.plot_anat(vol_corrected, display_mode='y', cut_coords=get_cut_cords(vol_corrected, n_slices=n_slices),
                           title='Corrected', black_bg=True, axes=axes[2])

        #path = Path.cwd() / 'fieldmap_correction_comparison.png'
        path = os.path.join(os.getcwd(), 'fieldmap_correction_comparison.png')
        plt.savefig(path, dpi=300)
        plt.close(fig)
        return path

    vol_main = pick_volume('vol_main', volume=volume)
    wf.connect('inputspec', 'main', vol_main, 'in_file')

    vol_fmap = pick_volume('vol_fmap', volume=volume)
    wf.connect('inputspec', 'fmap', vol_fmap, 'in_file')

    vol_corrected = pick_volume('vol_corrected', volume=volume)
    wf.connect('inputspec', 'func_corrected', vol_corrected, 'in_file')

    montage = Node(Function(
        input_names=['vol_main', 'vol_fmap', 'vol_corrected'],
        output_names=['out_file'],
        function=create_montage),
        name='montage_node'
    )
    wf.connect(vol_main, 'out_file', montage, 'vol_main')
    wf.connect(vol_fmap, 'out_file', montage, 'vol_fmap')
    wf.connect(vol_corrected, 'out_file', montage, 'vol_corrected')

    wf.connect(montage, 'out_file', 'outputspec', 'out_file')
    wf.connect(montage, 'out_file', 'sinker', 'qc_fieldmap_correction')
    

@QcPipeline(inputspec_fields=['background', 'overlay'],
            outputspec_fields=['out_file'])
def qc_fieldmap_correction_fugue(wf, overlay_volume='middle', **kwargs):
    """
    Generate a quality check (QC) image for the FUGUE fieldmap correction workflow.

    Parameters:
        overlay_volume (str): The volume of the overlay image to be used for the QC plot.
         Options are "first", "middle", "last", or an integer specifying the volume index.
         Default is "middle".

    Inputs:
        background (str): Path to the anatomical background image.
        overlay (str): Path to the overlay image (e.g., the unwarped functional scan).

    Outputs:
        out_file (str): Path to the generated QC image.

    Sinking:
        - Generated QC image showing the overlay on the background.
    """

    def create_fieldmap_plot(overlay, background):
        from PUMI.utils import plot_roi

        _, output_file = plot_roi(roi_img=overlay, bg_img=background)

        return output_file

    overlay_vol = pick_volume('overlay_vol', overlay_volume)
    wf.connect('inputspec', 'overlay', overlay_vol, 'in_file')

    overlay_bet = bet_deepbet('overlay_bet')
    wf.connect(overlay_vol, 'out_file', overlay_bet, 'in_file')

    plot = Node(Function(input_names=['overlay', 'background'],
                         output_names=['out_file'],
                         function=create_fieldmap_plot),
                name='plot')

    wf.connect('inputspec', 'background', plot, 'background')
    wf.connect(overlay_bet, 'out_file', plot, 'overlay')

    wf.connect(plot, 'out_file', 'sinker', 'qc_fieldmap_correction')

    # output
    wf.connect(plot, 'out_file', 'outputspec', 'out_file')

    
@FuncPipeline(inputspec_fields=['main', 'main_json', 'fmap', 'fmap_json'],
              outputspec_fields=['out_file'])
def fieldmap_correction_topup(wf, num_volumes=5, **kwargs):
    """

    Perform fieldmap correction on the functional data using FSL's TOPUP.

    Parameters:
        num_volumes (int): Number of volumes to extract from the main functional sequence for averaging.
                            Default is 5.

    Inputs:
        main (str): Path to the main functional image (e.g., 4D functional MRI data).
        main_json (str): Path to the JSON metadata for the main sequence.
        fmap (str): Path to the fieldmap image (e.g., 4D fieldmap data).
        fmap_json (str): Path to the JSON metadata for the fieldmap sequence.

    Outputs:
        out_file (str): Path to the corrected 4D functional image after fieldmap correction.

    Sinking:
        - Corrected functional sequence after fieldmap correction.
        - QC results for fieldmap correction.

    """

    # Extract how many volumes from the main sequence we are told to extract
    num_volumes = int(wf.cfg_parser.get('FIELDMAP-CORRECTION', 'num_volumes', fallback=num_volumes))

    # Extract the first num_volumes volumes from main sequence
    extract_main_volumes = Node(fsl.ExtractROI(t_min=0, t_size=num_volumes), name='extract_main_volumes')
    wf.connect('inputspec', 'main', extract_main_volumes, 'in_file')

    # Compute the mean of extracted main volumes
    mean_main = Node(fsl.MeanImage(), name='mean_main')
    wf.connect(extract_main_volumes, 'roi_file', mean_main, 'in_file')

    # Average all fieldmap volumes
    mean_fmap = Node(fsl.MeanImage(), name='mean_fmap')
    wf.connect('inputspec', 'fmap', mean_fmap, 'in_file')

    # Retrieve encoding direction, total readout time and repetition time
    def retrieve_image_params_function(main_json, fmap_json):
        import json

        with open(main_json, 'r') as f:
            main_metadata = json.load(f)

        with open(fmap_json, 'r') as f:
            fmap_metadata = json.load(f)

        for key in ['PhaseEncodingDirection', 'TotalReadoutTime', 'RepetitionTime']:
            main_value = main_metadata.get(key, None)
            fmap_value = fmap_metadata.get(key, None)

            if main_value is None:
                raise ValueError(f'JSON of main sequence is missing the key {key}!')

            if fmap_value is None:
                raise ValueError(f'JSON of fieldmap sequence is missing the key {key}!')

        main_encoding_direction = main_metadata.get('PhaseEncodingDirection')
        main_total_readout_time = main_metadata.get('TotalReadoutTime')
        main_repetition_time = main_metadata.get('RepetitionTime')

        fmap_encoding_direction = fmap_metadata.get('PhaseEncodingDirection')
        fmap_total_readout_time = fmap_metadata.get('TotalReadoutTime')
        fmap_repetition_time = fmap_metadata.get('RepetitionTime')

        if main_encoding_direction == fmap_encoding_direction:
            raise ValueError(f'Encoding direction of main sequence and fieldmap sequence are not allowed to be the same, but found {main_encoding_direction} and {fmap_encoding_direction}!')

        if main_total_readout_time != fmap_total_readout_time:
            raise ValueError(f'TRT of main sequence IS NOT EQUAL to fieldmap TRT ({main_total_readout_time}) != {fmap_total_readout_time})')

        if main_repetition_time != fmap_repetition_time:
            raise ValueError(f'TR of main sequence IS NOT EQUAL to fieldmap TR ({main_repetition_time}) != {fmap_repetition_time})')

        # In case we have Siemens j-notation instead of y, replace j by y
        main_encoding_direction = main_encoding_direction.replace('j', 'y')
        fmap_encoding_direction = fmap_encoding_direction.replace('j', 'y')

        encoding_direction = [main_encoding_direction, fmap_encoding_direction]
        total_readout_time = main_total_readout_time
        repetition_time = main_repetition_time

        return encoding_direction, total_readout_time, repetition_time

    retrieve_image_params = Node(
        utility.Function(
            input_names=['main_json', 'fmap_json'],
            output_names=['encoding_direction', 'total_readout_time', 'repetition_time'],
            function=retrieve_image_params_function
        ),
        name='retrieve_image_params'
    )
    wf.connect('inputspec', 'main_json', retrieve_image_params, 'main_json')
    wf.connect('inputspec', 'fmap_json', retrieve_image_params, 'fmap_json')

    def combine_items_to_list(item_1, item_2):
        return [item_1, item_2]

    avg_volumes_to_list = Node(Function(
        input_names=['item_1', 'item_2'],
        output_names=['output'],
        function=combine_items_to_list),
        name='avg_volumes_to_list'
    )
    wf.connect(mean_main, 'out_file', avg_volumes_to_list, 'item_1')
    wf.connect(mean_fmap, 'out_file', avg_volumes_to_list, 'item_2')

    # Combine averaged main and averaged fieldmap into a 4D image
    merge_avg_images = Node(fsl.Merge(dimension='t'), name='merge_avg_images')
    wf.connect(avg_volumes_to_list, 'output', merge_avg_images, 'in_files')
    wf.connect(retrieve_image_params, 'repetition_time', merge_avg_images, 'tr')

    # Estimate susceptibility induced distortions
    topup = Node(fsl.TOPUP(), name='topup')
    wf.connect(merge_avg_images, 'merged_file', topup, 'in_file')
    wf.connect(retrieve_image_params, 'total_readout_time', topup, 'readout_times')
    wf.connect(retrieve_image_params, 'encoding_direction', topup, 'encoding_direction')

    # Apply result of fsl.TOPUP to our original data
    # Result will be one 4D distortion corrected image
    apply_topup = Node(fsl.ApplyTOPUP(method='jac'), name='apply_topup')
    wf.connect('inputspec', 'main', apply_topup, 'in_files')
    wf.connect(topup, 'out_fieldcoef', apply_topup, 'in_topup_fieldcoef')
    wf.connect(topup, 'out_movpar', apply_topup, 'in_topup_movpar')
    wf.connect(topup, 'out_enc_file', apply_topup, 'encoding_file')

    qc_fieldmap_correction = qc_fieldmap_correction_topup('qc_fieldmap_correction')
    wf.connect('inputspec', 'main', qc_fieldmap_correction, 'main')
    wf.connect('inputspec', 'fmap', qc_fieldmap_correction, 'fmap')
    wf.connect(topup, 'out_corrected', qc_fieldmap_correction, 'func_corrected')

    wf.connect(apply_topup, 'out_corrected', 'outputspec', 'out_file')
    wf.connect(apply_topup, 'out_corrected', 'sinker', 'out_file')

    
@FuncPipeline(inputspec_fields=['main_img', 'main_json', 'anat_img', 'phasediff_img', 'phasediff_json',
                                'magnitude_img'],
              outputspec_fields=['out_file'])
def fieldmap_correction_fugue(wf, **kwargs):
    """
    Perform fieldmap correction using FSL's FUGUE.

    This pipeline uses the magnitude and phase-difference images to generate a fieldmap and then applies
    fieldmap correction to a functional image.

    Inputs:
        main_img (str): Path to the 4D functional image to be corrected.
        main_json (str): Path to the JSON metadata file for the functional image.
        anat_img (str): Path to the anatomical image for QC background.
        phasediff_img (str): Path to the phase-difference image.
        phasediff_json (str): Path to the JSON metadata file for the phase-difference image.
        magnitude_img (str): Path to the magnitude image.

    Outputs:
        out_file (str): Path to the fieldmap-corrected functional image.

    Sinking:
        - Fieldmap-corrected functional image.
        - QC images for the fieldmap correction.

    """

    bet_magnitude_img = bet_deepbet('bet_magnitude_img', sinking_name='magnitude_img_segm')
    wf.connect('inputspec', 'magnitude_img', bet_magnitude_img, 'in_file')

    def get_fieldmap_parameters(main_json, phasediff_json):
        import json

        with open(main_json, 'r') as f:
            main_metadata = json.load(f)

        with open(phasediff_json, 'r') as f:
            phasediff_metadata = json.load(f)

        # Extract dwell_time (EffectiveEchoSpacing)
        dwell_time = main_metadata.get('EffectiveEchoSpacing')  # In seconds

        if dwell_time is None:
            raise ValueError(f'{main_json} does not contain EffectiveEchoSpacing')

        # Extract and calculate delta_TE (in ms)
        echo_time_1 = phasediff_metadata.get('EchoTime1')  # In seconds
        echo_time_2 = phasediff_metadata.get('EchoTime2')  # In seconds

        if echo_time_1 is None:
            raise ValueError(f'{main_json} does not contain EchoTime1')

        if echo_time_2 is None:
            raise ValueError(f'{main_json} does not contain EchoTime2')

        asym_se_time = abs(echo_time_2 - echo_time_1) # In seconds
        delta_TE = asym_se_time * 1000  # Convert to ms

        return dwell_time, delta_TE, asym_se_time

    get_params = Node(Function(
        input_names=['main_json', 'phasediff_json'],
        output_names=['dwell_time', 'delta_TE', 'asym_se_time'],
        function=get_fieldmap_parameters
    ), name='get_params')
    wf.connect('inputspec', 'phasediff_json', get_params, 'phasediff_json')
    wf.connect('inputspec', 'main_json', get_params, 'main_json')

    prepare_fieldmap = Node(fsl.PrepareFieldmap(), name='prepare_fieldmap')
    wf.connect(get_params, 'delta_TE', prepare_fieldmap, 'delta_TE')
    wf.connect(bet_magnitude_img, 'out_file', prepare_fieldmap, 'in_magnitude')
    wf.connect('inputspec', 'phasediff_img', prepare_fieldmap, 'in_phase')

    fugue = Node(fsl.FUGUE(), name='fugue')
    wf.connect(get_params, 'dwell_time', fugue, 'dwell_time')
    wf.connect(get_params, 'asym_se_time', fugue, 'asym_se_time')
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

