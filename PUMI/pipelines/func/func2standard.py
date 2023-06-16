import nipype.interfaces.utility as utility
from PUMI.engine import FuncPipeline, NestedNode as Node, QcPipeline
from PUMI.pipelines.multimodal.image_manipulation import vol2png
from PUMI.plot.carpet_plot import plot_carpet
from nipype.interfaces import fsl, ants
from nipype.interfaces.c3 import C3dAffineTool
import os



@QcPipeline(inputspec_fields=['warped_image', 'example_func', 'func', 'atlas', 'confounds'],
            outputspec_fields=['out_file'])
def qc(wf, carpet_plot=True, **kwargs):
    qc_vol2png = vol2png(wf.name + '_vol2png')
    wf.connect('inputspec', 'warped_image', qc_vol2png, 'overlay_image')
    wf.connect('inputspec', 'example_func', qc_vol2png, 'bg_image')

    if carpet_plot:
        carpet_node = Node(
            utility.Function(
                input_names=['img', 'save_carpet'],
                output_names=['ax1'],
                function=plot_carpet
            ),
            name=wf.name + '_carpet_plot'
        )
        carpet_node.inputs.save_carpet = True
        wf.connect('inputspec', 'func', carpet_node, 'img')
        # todo: support 'atlas' and 'confounds' parameter in carpet plot

    #  Output
    wf.connect(qc_vol2png, 'out_file', 'outputspec', 'out_file')

    # sinking
    wf.connect(qc_vol2png, 'out_file', 'sinker', wf.name)



@FuncPipeline(inputspec_fields=['atlas', 'anat', 'linear_reg_mtrx', 'nonlinear_reg_mtrx', 'func',
                                'example_func', 'confounds', 'confound_names'],
              outputspec_fields=['out_file'])
def func2standard(wf, stdreg='ants', interp="NearestNeighbor", carpet_plot=True, **kwargs):
    """

    Apply transformation to standard space

        Parameters:
            stdreg (str): registration tools ('ants' and 'fsl' possible values)
            interp (str): interpolation method
            carpet_plot (bool): set to True, to generate carpet plots
        Inputs:
            atlas (str): Path to the atlas file
            anat ([str]): Path to the anatomical scan
            linear_reg_mtrx ([str]): Path to linear registration matrix
            nonlinear_reg_mtrx ([str]): Path to nonlinear registration matrix
            func ([str]): Path to functional image
            example_func ([str]): Path to an example volume of the functional scan
            confounds ([str]): Confounds
            confound_names ([str]): Name of the confounds
       Returns:
           out_file (str): Image in standard space

    Adapted from Balint Kincses (2018) code
    """

    wf.get_node('inputspec').inputs.reference_brain = os.path.join(
        os.environ['FSLDIR'],
        "data/standard/MNI152_T1_3mm_brain.nii.gz" # 3mm by default
    )

    if stdreg == 'fsl':
        applywarp = Node(interface=fsl.ApplyWarp(interp=interp, ), name='applywarp')
        wf.connect('inputspec', 'atlas', applywarp, 'in_file')
        wf.connect('inputspec', 'linear_reg_mtrx', applywarp, 'postmat')
        wf.connect('inputspec', 'nonlinear_reg_mtrx', applywarp, 'field_file')
        wf.connect('inputspec', 'example_func', applywarp, 'ref_file')
    elif stdreg == 'ants':
        # concat premat and ants transform
        bbr2ants = Node(interface=C3dAffineTool(fsl2ras=True, itk_transform=True), name="bbr2ants")
        wf.connect('inputspec', 'anat', bbr2ants, 'source_file')
        wf.connect('inputspec', 'linear_reg_mtrx', bbr2ants, 'transform_file')
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
        wf.connect('inputspec', 'nonlinear_reg_mtrx', transform_list, 'trf_first')

        applywarp = Node(interface=ants.ApplyTransforms(interpolation=interp, input_image_type=3), name='applywarp')
        wf.connect(transform_list, 'trflist', applywarp, 'transforms')
        wf.connect('inputspec', 'atlas', applywarp, 'input_image')
        wf.connect('inputspec', 'example_func', applywarp, 'reference_image')
    else:
        raise ValueError(f'%s is not a valid option for stdreg! Please choose \'fsl\' or \'ants\'!' % stdreg)

    qc_func2std = qc('qc_' + wf.name, carpet_plot=carpet_plot)
    if stdreg == 'fsl':
        wf.connect(applywarp, 'out_file', qc_func2std, 'warped_image')
    elif stdreg == 'ants':
        wf.connect(applywarp, 'output_image', qc_func2std, 'warped_image')
    wf.connect('inputspec', 'example_func', qc_func2std, 'example_func')

    if carpet_plot:
        wf.connect('inputspec', 'func', qc_func2std, 'func')
        wf.connect('inputspec', 'atlas', qc_func2std, 'atlas')
        wf.connect('inputspec', 'confounds', qc_func2std, 'confounds')

    # Output
    if stdreg == 'fsl':
        wf.connect(applywarp, 'out_file', 'outputspec', 'out_file')
    elif stdreg == 'ants':
        wf.connect(applywarp, 'output_image', 'outputspec', 'out_file')

    # Sinking
    if stdreg == 'fsl':
        wf.connect(applywarp, 'out_file', 'sinker', 'func2std')
    elif stdreg == 'ants':
        wf.connect(applywarp, 'output_image', 'sinker', 'func2std')


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

    qc_atlas2func = qc('qc_' + wf.name, carpet_plot=carpet_plot)
    if stdreg == 'fsl':
        wf.connect(applywarp, 'out_file', qc_atlas2func, 'warped_image')
    elif stdreg == 'ants':
        wf.connect(applywarp, 'output_image', qc_atlas2func, 'warped_image')
    wf.connect('inputspec', 'example_func', qc_atlas2func, 'example_func')

    if carpet_plot:
        wf.connect('inputspec', 'func', qc_atlas2func, 'func')
        wf.connect('inputspec', 'atlas', qc_atlas2func, 'atlas')
        wf.connect('inputspec', 'confounds', qc_atlas2func, 'confounds')

    # Output
    if stdreg == 'fsl':
        wf.connect(applywarp, 'out_file', 'outputspec', 'atlas2func')
    elif stdreg == 'ants':
        wf.connect(applywarp, 'output_image', 'outputspec', 'atlas2func')

    # Sinking
    if stdreg == 'fsl':
        wf.connect(applywarp, 'out_file', 'sinker', 'atlas2func')
    elif stdreg == 'ants':
        wf.connect(applywarp, 'output_image', 'sinker', 'atlas2func')

