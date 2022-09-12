import nipype.interfaces.utility as utility
from PUMI.engine import FuncPipeline, NestedNode as Node, QcPipeline
from PUMI.pipelines.multimodal.image_manipulation import vol2png
from PUMI.plot.carpet_plot import plot_carpet
from PUMI.utils import relabel_atlas, get_reference
from nipype.interfaces import fsl, ants
from nipype.interfaces.c3 import C3dAffineTool
import os


@QcPipeline(inputspec_fields=['warped_image', 'example_func', 'func', 'atlas', 'confounds'],
            outputspec_fields=[])
def atlas2func_qc(wf, carpet_plot=True, **kwargs):
    atlas2func_vol2png = vol2png('atlas2func_vol2png')
    wf.connect('inputspec', 'warped_image', atlas2func_vol2png, 'overlay_image')
    wf.connect('inputspec', 'example_func', atlas2func_vol2png, 'bg_image')

    # todo: create carpet plot

    """
    if carpet_plot:
        altas2func_carpet_plot = plot_carpet('altas2func_carpet_plot')
        wf.connect('inputspec', 'func', altas2func_carpet_plot, 'inputspec.func')
        wf.connect('inputspec', 'atlas', altas2func_carpet_plot, 'inputspec.atlas')
        wf.connect('inputspec', 'confounds', altas2func_carpet_plot, 'inputspec.confounds')
    """


@FuncPipeline(inputspec_fields=['atlas', 'anat', 'inv_linear_reg_mtrx', 'inv_nonlinear_reg_mtrx', 'func',
                                'example_func', 'confounds', 'confound_names'],
              outputspec_fields=['atlas2func'])
def atlas2func(wf, stdreg='ants', interp="NearestNeighbor", carpet_plot=True, **kwargs):
    """

    Relabel atlas
        * Beware: atlas, confounds and confound_names are optional inputs
        Parameters:
            stdreg (str): registration tools ('ants' and 'fsl' possible values)
            interp (str):
            carpet_plot (bool):
        Inputs:
            atlas (str): Path to the atlas file
            anat ([str]):
            inv_linear_reg_mtrx ([str]):
            inv_nonlinear_reg_mtrx ([str]):
            func ([str]):
            example_func ([str]):
            confounds ([str]):
            confound_names ([str]):
       Returns:
           atlas2func (str):
    Adapted from Balint Kincses (2018)
    """

    # todo: complete documentation
    # todo: add qc

    wf.get_node('inputspec').inputs.reference_brain = os.path.join(
        os.environ['FSLDIR'],
        "data/standard/MNI152_T1_3mm_brain.nii.gz" # 3mm by default
    )

    if stdreg == 'fsl':
        applywarp = Node(interface=fsl.ApplyWarp(interp=interp, ), name='applywarp')

        wf.connect('inputspec', 'atlas', applywarp, 'in_file')
        wf.connect('inputspec', 'inv_linear_reg_mtrx', applywarp, 'postmat')
        wf.connect('inputspec', 'inv_nonlinear_reg_mtrx', applywarp, 'field_file')
        wf.connect('inputspec', 'example_func', applywarp, 'ref_file')
        wf.connect(applywarp, 'out_file', 'outputspec', 'atlas2func')

        wf.connect(applywarp, 'out_file', 'sinker', 'atlas2func')
    elif stdreg == 'ants':
        # concat premat and ants transform
        bbr2ants = Node(interface=C3dAffineTool(fsl2ras=True, itk_transform=True), name="bbr2ants")
        wf.connect('inputspec', 'anat', bbr2ants, 'source_file')
        wf.connect('inputspec', 'inv_linear_reg_mtrx', bbr2ants, 'transform_file')
        wf.connect('inputspec', 'example_func', bbr2ants, 'reference_file')

        #concat trfs into a list
        transform_list = Node(
            interface=utility.Function(
                input_names=['trf_first', 'trf_second'],
                output_names=['trflist'],
                function=lambda trf_first, trf_second: [trf_second, trf_first]
            ), name="collect_trf"
        )
        wf.connect(bbr2ants, 'itk_transform', transform_list, 'trf_second')
        wf.connect('inputspec', 'inv_nonlinear_reg_mtrx', transform_list, 'trf_first')

        applywarp = Node(interface=ants.ApplyTransforms(interpolation=interp, input_image_type=3), name='applywarp')
        wf.connect(transform_list, 'trflist', applywarp, 'transforms')
        wf.connect('inputspec', 'atlas', applywarp, 'input_image')
        wf.connect('inputspec', 'example_func', applywarp, 'reference_image')
    else:
        raise ValueError(f'%s is not a valid option for stdreg! Please choose \'fsl\' or \'ants\'!' % stdreg)

    qc = atlas2func_qc('atlas2func_qc', carpet_plot=carpet_plot)
    if stdreg == 'fsl':
        wf.connect(applywarp, 'out_file', qc, 'warped_image')
    elif stdreg == 'ants':
        wf.connect(applywarp, 'output_image', qc, 'warped_image')
    wf.connect('inputspec', 'example_func', qc, 'example_func')

    if carpet_plot:
        wf.connect('inputspec', 'func', qc, 'func')
        wf.connect('inputspec', 'atlas', qc, 'atlas')
        wf.connect('inputspec', 'confounds', qc, 'confounds')

    # Output
    if stdreg == 'fsl':
        wf.connect(applywarp, 'out_file', 'outputspec', 'atlas2func')
    elif stdreg == 'ants':
        wf.connect(applywarp, 'output_file', 'sinker', 'atlas2func')

    # Sinking
    if stdreg == 'fsl':
        wf.connect(applywarp, 'out_file', 'sinker', 'atlas2func')
    elif stdreg == 'ants':
        wf.connect(applywarp, 'output_image', 'sinker', 'atlas2func')

