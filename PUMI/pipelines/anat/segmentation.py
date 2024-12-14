from PUMI.engine import AnatPipeline, QcPipeline
from PUMI.interfaces.HDBet import HDBet
from PUMI.utils import create_segmentation_qc
from nipype.interfaces import fsl
from nipype.interfaces.utility import Split
from matplotlib.colors import LinearSegmentedColormap
from nipype import Function
from PUMI.engine import AnatPipeline
from PUMI.engine import NestedNode as Node
import os
from PUMI.pipelines.multimodal.image_manipulation import pick_volume
from nipype.interfaces import utility



@QcPipeline(inputspec_fields=['background', 'overlay'],
            outputspec_fields=['out_file'])
def qc_segmentation(wf, fmri=False, **kwargs):
    """

    Create quality check images for background extraction workflows

    Inputs:
        background (str): Path to the extracted brain.
        overlay (str): Path to the overlay.

    Outputs:
        out_file (str): Path to the quality check image

    Sinking:
    -   The quality check image

    """
    plot = Node(Function(input_names=['overlay', 'bg_img', 'cmap'],
                         output_names=['out_file'],
                         function=create_segmentation_qc),
                name='plot')
    wf.connect('inputspec', 'background', plot, 'bg_img')
    wf.connect('inputspec', 'overlay', plot, 'overlay')

    # sinking
    if fmri:
        wf.connect(plot, 'out_file', 'sinker', 'qc_func_segmentation')
    else:
        wf.connect(plot, 'out_file', 'sinker', 'qc_anat_segmentation')

    # output
    wf.connect(plot, 'out_file', 'outputspec', 'out_file')


@QcPipeline(inputspec_fields=['in_file'],
            outputspec_fields=['out_file'])
def qc_tissue_segmentation(wf, **kwargs):
    """

    Create quality check images for tissue segmentation workflows

    Inputs:
        in_file (str): Path to the partial volume map

    Outputs:
        out_file (str): Path to the quality check image

    Sinking:
    -   The quality check image

    """
    plot = Node(Function(input_names=['overlay', 'cmap'],
                         output_names=['out_file'],
                         function=create_segmentation_qc),
                name='plot')
    colors = ['#00A859', '#FFCC29', '#3E4095']
    plot.inputs.cmap = LinearSegmentedColormap.from_list('tissue_segmentation_colors', colors, N=3)
    wf.connect('inputspec', 'in_file', plot, 'overlay')

    # sinking
    wf.connect(plot, 'out_file', 'sinker', 'qc_tissue_segmentation')

    # output
    wf.connect(plot, 'out_file', 'outputspec', 'out_file')


@AnatPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file', 'brain_mask'])
def bet_fsl(wf, fmri=False, volume='middle', **kwargs):
    """

    Perform brain extraction with FSL.

    Parameters:
        fmri (bool): Set to true if the supplied in_file file is a 4D volume.
        volume (str/int): On which volume to perform the brain extraction based on if a 4D image is supplied.
                          Can be either 'first', 'middle', 'last', 'mean' or a number.

    Inputs:
        in_file(str): Path to the 3D or 4D head scan.

    Outputs:
        out_file(str): Path to the extracted brain.
        brain_mask (str): Path to the mask of the extracted brain.

    """

    # bet
    bet = Node(interface=fsl.BET(), name='bet')
    bet.inputs.mask = True
    bet.inputs.vertical_gradient = wf.cfg_parser.getfloat('FSL', 'bet_vertical_gradient', fallback=-0.3)
    wf.connect('inputspec', 'in_file', bet, 'in_file')

    if fmri:
        bet.inputs.frac = wf.cfg_parser.getfloat('FSL', 'bet_frac_func', fallback=0.3)
        bet.inputs.functional = True

        bet_vol = pick_volume('bet_vol', volume=volume)
        wf.connect(bet, 'mask_file', bet_vol, 'in_file')

        apply_mask = Node(fsl.ApplyMask(), name="apply_mask")
        wf.connect(bet_vol, 'out_file', apply_mask, 'mask_file')
        wf.connect('inputspec', 'in_file', apply_mask, 'in_file')
    else:
        bet.inputs.frac = wf.cfg_parser.getfloat('FSL', 'bet_frac_anat', fallback=0.3)
        bet.inputs.robust = True

    # quality check
    if fmri:

        overlay = pick_volume('qc_overlay', volume=volume)
        wf.connect(apply_mask, 'out_file', overlay, 'in_file')

        background = pick_volume('qc_background', volume=volume)
        wf.connect('inputspec', 'in_file', background, 'in_file')

        qc = qc_segmentation(name='qc_segmentation', fmri=True, qc_dir=wf.qc_dir)
        wf.connect(overlay, 'out_file', qc, 'overlay')
        wf.connect(background, 'out_file', qc, 'background')
        #wf.connect(overlay, 'out_file', qc, 'background')
        #wf.connect(background, 'out_file', qc, 'overlay')
    else:
        qc = qc_segmentation(name='qc_segmentation', qc_dir=wf.qc_dir)
        wf.connect(bet, 'out_file', qc, 'overlay')
        wf.connect('inputspec', 'in_file', qc, 'background')

    # sinking
    wf.connect(bet, 'out_file', 'sinker', 'out_file')
    wf.connect(bet, 'mask_file', 'sinker', 'mask_file')

    # output
    wf.connect(bet, 'mask_file', 'outputspec', 'brain_mask')
    if fmri:
        wf.connect(apply_mask, 'out_file', 'outputspec', 'out_file')
    else:
        wf.connect(bet, 'out_file', 'outputspec', 'out_file')


@AnatPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file', 'brain_mask', 'tiv'])
def bet_deepbet(wf, fmri=False, volume='middle', threshold=0.5, n_dilate=0, no_gpu=False, **kwargs):
    """

    Perform brain extraction with deepbet.

    Parameters:
        fmri (bool): Set to true if the supplied in_file file is a 4D volume.
        volume (str/int): On which volume to perform the brain extraction based on if a 4D image is supplied.
                          Can be either 'first', 'middle', 'last', 'mean' or a number.
        threshold (int): Threshold value of deepbet.
        n_dilate (int): n_dilate value of deepbet.
                        Adjusting the size of the brain mask by either adding or removing adjacent voxels along its
                        surface.
        no_gpu (bool): If a graphics card is installed but should not be used for the extraction, set no_gpu to true.

    Inputs:
        in_file(str): Path to the 3D or 4D head scan.

    Outputs:
        out_file(str): Path to the extracted brain.
        brain_mask (str): Path to the mask of the extracted brain.
        tiv (str): Path to file containing total intracranial volume (TIV) in cm³.

    For more information regarding see: https://github.com/wwu-mmll/deepbet

    """

    def run_deepbet(in_file, threshold=0.5, n_dilate=0, no_gpu=False):
        from deepbet import run_bet
        from pathlib import Path
        import os

        input_filename = os.path.basename(in_file)  # x/y/sub_11.nii.gz -> sub_11.nii.gz
        input_filename = input_filename.split('.')[0]  # sub_11.nii.gz -> sub_11

        brain_path = Path(os.getcwd() + '/' + input_filename + '_bet.nii.gz')  # where to store extracted brain
        mask_path = Path(os.getcwd() + '/' + input_filename + '_bet_mask.nii.gz')
        tiv_path = Path(os.getcwd() + '/' + input_filename + '_bet_tiv.csv')

        run_bet(input_paths=[in_file],
                brain_paths=[brain_path],
                mask_paths=[mask_path],
                tiv_paths=[tiv_path],
                threshold=threshold,
                n_dilate=n_dilate,
                no_gpu=no_gpu)

        return str(brain_path), str(mask_path), str(tiv_path)

    bet = Node(
        interface=utility.Function(
            input_names=['in_file', 'threshold', 'n_dilate', 'no_gpu'],
            output_names=['out_file', 'brain_mask', 'tiv'],
            function=run_deepbet
        ),
        name='bet'
    )
    wf.connect('inputspec', 'in_file', bet, 'in_file')
    bet.inputs.threshold = threshold
    bet.inputs.n_dilate = n_dilate
    bet.inputs.no_gpu = no_gpu

    if fmri:
        bet_vol = pick_volume('bet_vol', volume=volume)
        wf.connect(bet, 'brain_mask', bet_vol, 'in_file')

        apply_mask = Node(fsl.ApplyMask(), name="apply_mask")
        wf.connect(bet_vol, 'out_file', apply_mask, 'mask_file')
        wf.connect('inputspec', 'in_file', apply_mask, 'in_file')

        overlay = pick_volume('qc_overlay', volume=volume)
        wf.connect(apply_mask, 'out_file', overlay, 'in_file')

        background = pick_volume('qc_background', volume=volume)
        wf.connect('inputspec', 'in_file', background, 'in_file')

        qc = qc_segmentation(name='qc_segmentation', fmri=True, qc_dir=wf.qc_dir)
        wf.connect(overlay, 'out_file', qc, 'overlay')
        wf.connect(background, 'out_file', qc, 'background')
    else:
        qc = qc_segmentation(name='qc_segmentation', qc_dir=wf.qc_dir)
        wf.connect(bet, 'out_file', qc, 'overlay')
        wf.connect('inputspec', 'in_file', qc, 'background')

    # sinking
    wf.connect(bet, 'out_file', 'sinker', 'out_file')
    wf.connect(bet, 'brain_mask', 'sinker', 'brain_mask')
    wf.connect(bet, 'tiv', 'sinker', 'tiv')

    # output
    wf.connect(bet, 'brain_mask', 'outputspec', 'brain_mask')
    wf.connect(bet, 'tiv', 'outputspec', 'tiv')
    if fmri:
        wf.connect(apply_mask, 'out_file', 'outputspec', 'out_file')
    else:
        wf.connect(bet, 'out_file', 'outputspec', 'out_file')




@AnatPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file', 'brain_mask'])
def bet_hd(wf, **kwargs):
    """
    Does brain extraction with HD-Bet.
    """

    # bet
    bet = Node(interface=HDBet(), name='bet')
    bet.inputs.mode = kwargs.get('mode', wf.cfg_parser.get('HD-Bet', 'mode', fallback='accurate'))
    bet.inputs.device = kwargs.get('device', wf.cfg_parser.get('HD-Bet', 'device', fallback='0'))
    bet.inputs.tta = kwargs.get('tta', wf.cfg_parser.getint('HD-Bet', 'tta', fallback=1))
    bet.inputs.postprocessing = kwargs.get('postprocessing',
                                           wf.cfg_parser.getint('HD-Bet', 'postprocessing', fallback=1))
    bet.inputs.save_mask = kwargs.get('save_mask', wf.cfg_parser.getint('HD-Bet', 'save_mask', fallback=1))
    bet.inputs.overwrite_existing = kwargs.get('overwrite_existing',
                                               wf.cfg_parser.getint('HD-Bet', 'overwrite_existing', fallback=1))

    wf.connect('inputspec', 'in_file', bet, 'in_file')

    # quality check
    qc = qc_segmentation(name='qc_segmentation', qc_dir=wf.qc_dir)
    wf.connect('inputspec', 'in_file', qc, 'background')
    wf.connect(bet, 'out_file', qc, 'overlay')

    wf.connect(bet, 'out_file', 'outputspec', 'out_file')
    wf.connect(bet, 'mask_file', 'outputspec', 'brain_mask')


@AnatPipeline(inputspec_fields=['brain', 'stand2anat_xfm'],
              outputspec_fields=['probmap_csf', 'probmap_gm', 'probmap_wm', 'mixeltype', 'parvol_csf', 'parvol_gm',
                                 'parvol_wm', 'partial_volume_map'])
def tissue_segmentation_fsl(wf, priormap=True, **kwargs):
    """

    Perform segmentation of a brain extracted T1w image.

    Parameters:
        priormap (bool): Set to True if you want to use prior probability maps.
                         In that case the stand2anat_xfm input is needed (otherwise not).

    Inputs:
        brain (str): Path to the brain which should be segmented.
        stand2anat_xfm (str): Path to standard2input matrix calculated by FSL FLIRT.
                              Only necessary when using prior probability maps!

    Outputs:
        probmap_csf (str): Path to csf probability map.
        probmap_gm (str): Path to gm probability map.
        probmap_wm (str): Path to wm probability map
        mixeltype (str): Path to mixeltype volume file
        parvol_csf (str): Path to csf partial volume file
        parvol_gm (str): Path to gm partial volume file
        parvol_wm (str): Path to wm partial volume file
        partial_volume_map (str): Path to partial volume map

    Sinking:
    - The probability maps for csf, gm and wm.

    Acknowledgements:
        Modified version of CPAC.seg_preproc.seg_preproc (https://github.com/FCP-INDI/C-PAC) and Balint Kinces code (2018)

    For a deeper insight:
        - https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST
        - https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.fsl.preprocess.html

     """

    if priormap:
        priorprob_csf = os.path.join(os.environ['FSLDIR'], '/data/standard/tissuepriors/avg152T1_csf.hdr')
        priorprob_gm = os.path.join(os.environ['FSLDIR'], '/data/standard/tissuepriors/avg152T1_gray.hdr')
        priorprob_wm = os.path.join(os.environ['FSLDIR'], '/data/standard/tissuepriors/avg152T1_white.hdr')

    fast = Node(interface=fsl.FAST(), name='fast')
    fast.inputs.img_type = 1
    fast.inputs.segments = True
    fast.inputs.probability_maps = True
    fast.inputs.out_basename = 'fast'
    wf.connect('inputspec', 'brain', fast, 'in_files')
    if priormap:
        wf.connect('inputspec', 'stand2anat_xfm', fast, 'init_transform')

    split_probability_maps = Node(interface=Split(), name='split_probability_maps')
    split_probability_maps.inputs.splits = [1, 1, 1]
    split_probability_maps.inputs.squeeze = True
    wf.connect(fast, 'probability_maps', split_probability_maps, 'inlist')

    split_partial_volume_files = Node(interface=Split(), name='split_partial_volume_files')
    split_partial_volume_files.inputs.splits = [1, 1, 1]
    split_partial_volume_files.inputs.squeeze = True
    wf.connect(fast, 'partial_volume_files', split_partial_volume_files, 'inlist')

    qc = qc_tissue_segmentation(name='qc', qc_dir=wf.qc_dir)
    wf.connect(fast, 'partial_volume_map', qc, 'in_file')

    # sinking
    wf.connect(split_probability_maps, 'out1', 'sinker', 'fast_csf')
    wf.connect(split_probability_maps, 'out2', 'sinker', 'fast_gm')
    wf.connect(split_probability_maps, 'out3', 'sinker', 'fast_wm')

    # output
    wf.get_node('outputspec').inputs.probmap_csf = priorprob_csf
    wf.get_node('outputspec').inputs.probmap_gm = priorprob_gm
    wf.get_node('outputspec').inputs.probmap_wm = priorprob_wm
    wf.connect(fast, 'mixeltype', 'outputspec', 'mixeltype')
    wf.connect(fast, 'partial_volume_map', 'outputspec', 'partial_volume_map')
    wf.connect(split_probability_maps, 'out1', 'outputspec', 'probmap_csf')
    wf.connect(split_probability_maps, 'out2', 'outputspec', 'probmap_gm')
    wf.connect(split_probability_maps, 'out3', 'outputspec', 'probmap_wm')
    wf.connect(split_partial_volume_files, 'out1', 'outputspec', 'parvol_csf')
    wf.connect(split_partial_volume_files, 'out2', 'outputspec', 'parvol_gm')
    wf.connect(split_partial_volume_files, 'out3', 'outputspec', 'parvol_wm')



def pydeface_wrapper(infile, force):
    """
    Workaround to store the defaced image in the correct place with useful name
    """
    from pydeface import utils


    outfile = os.path.join(os.getcwd(), 'defaced_' + os.path.basename(infile))
    warped_mask_img, warped_mask, template_reg, template_reg_mat = utils.deface_image(infile=infile,
                                                                                      outfile=outfile,
                                                                                      force=force)
    return outfile, warped_mask


'''
Pipline for defacing anatomical images

in_file : String
    Path to anat image

outfile : String
    Path to anat image
    If not specified, the output will be stored in the folder of the input.

deface_mask : String
    Path to defacing mask

'''


@AnatPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file', 'deface_mask'])
def defacing(wf, **kwargs):

    """
    Pipeline for defacing anatomical images.
    Also creates quality check images

    Inputs
        in_file(str): Path to anat image.

    Outputs
        out_file(nii.gz) : Defaced anatomical image

        deface_mask(str): Path to the defacing mask.

    Sinker
    -   Defaced anatomical image

    """

    deface_node = Node(Function(input_names=['infile', 'force'],
                                output_names=['warped_mask_img', 'warped_mask'],
                                function=pydeface_wrapper,
                                imports=[
                                    'import sys', 'import shutil', 'from nipype.interfaces import fsl',
                                    'from pydeface.utils import initial_checks, output_checks, generate_tmpfiles',
                                    'from pydeface.utils import cleanup_files, get_outfile_type, generate_tmpfiles',
                                    'from nibabel import load, Nifti1Image', 'import os']
                                ),
                       name='deface_node')

    # If set to True, the previous defaced img will be overwritten
    deface_node.inputs.force = True

    wf.connect('inputspec', 'in_file', deface_node, 'infile')

    # Quality Check
    defacing_qc = qc_segmentation(name='defacing_qc', qc_dir=wf.qc_dir)
    wf.connect('inputspec', 'in_file', defacing_qc, 'background')
    wf.connect(deface_node, 'warped_mask', defacing_qc, 'overlay')

    # Sink defaced image
    wf.connect('deface_node', 'warped_mask_img', 'sinker', 'defaced')

    wf.connect('deface_node', 'warped_mask_img', 'outputspec', 'out_file')
    wf.connect('deface_node', 'warped_mask', 'outputspec', 'deface_mask')