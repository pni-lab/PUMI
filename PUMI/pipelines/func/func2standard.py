import nipype.interfaces.utility as utility
from PUMI.engine import FuncPipeline, NestedNode as Node, QcPipeline
from PUMI.pipelines.multimodal.image_manipulation import vol2png
from PUMI.plot.carpet_plot import plot_carpet
from nipype.interfaces import fsl, ants
from nipype.interfaces.c3 import C3dAffineTool
import os



@QcPipeline(inputspec_fields=['overlay', 'func'],
            outputspec_fields=['out_file'])
def qc(wf, **kwargs):

    qc_vol2png = vol2png(wf.name + '_vol2png')
    wf.connect('inputspec', 'overlay', qc_vol2png, 'overlay_image')
    wf.connect('inputspec', 'func', qc_vol2png, 'bg_image')

    #  Output
    wf.connect(qc_vol2png, 'out_file', 'outputspec', 'out_file')

    # sinking
    wf.connect(qc_vol2png, 'out_file', 'sinker', wf.name)


@FuncPipeline(inputspec_fields=['anat', 'linear_reg_mtrx', 'nonlinear_reg_mtrx', 'func', 'reference_brain'],
              outputspec_fields=['out_file'])
def func2standard(wf, func_is_3D=True, stdreg='ants', interp="NearestNeighbor", **kwargs):
    """

    Apply transformation to standard space

    CAUTION: Make sure to set func_is_3D correctly!

        Parameters:
            stdreg (str): registration tools ('ants' and 'fsl' possible values)
            interp (str): interpolation method
            carpet_plot (bool): set to True, to generate carpet plots
        Inputs:
            anat (str): Path to the anatomical scan
            linear_reg_mtrx (str): Path to linear registration matrix
            nonlinear_reg_mtrx (str): Path to nonlinear registration matrix
            func (str): Path to functional image
            func_is_3D (bool): Set to False, if you supply 4D timeseries. Then no qc images are generated
            reference_brain (str): Path to reference brain image
       Returns:
           out_file (str): Image in standard space

    Adapted from Balint Kincses (2018) code
    """

    if wf.get_node('inputspec').inputs.reference_brain is None:
        wf.get_node('inputspec').inputs.reference_brain = os.path.join(
            os.environ['FSLDIR'],
            "data/standard/MNI152_T1_3mm_brain.nii.gz" # 3mm by default
    )

    if stdreg == 'fsl':
        applywarp = Node(interface=fsl.ApplyWarp(interp=interp, ), name='applywarp')
        wf.connect('inputspec', 'func', applywarp, 'in_file')  # example func
        wf.connect('inputspec', 'linear_reg_mtrx', applywarp, 'premat')
        wf.connect('inputspec', 'nonlinear_reg_mtrx', applywarp, 'field_file')
        wf.connect('inputspec', 'func', applywarp, 'ref_file')
    elif stdreg == 'ants':
        # concat premat and ants transform
        bbr2ants = Node(interface=C3dAffineTool(fsl2ras=True, itk_transform=True), name="bbr2ants")
        wf.connect('inputspec', 'func', bbr2ants, 'source_file')  # example func for source file
        wf.connect('inputspec', 'linear_reg_mtrx', bbr2ants, 'transform_file')
        wf.connect('inputspec', 'anat', bbr2ants, 'reference_file')  # anat for ref

        #concat trfs into a list
        transform_list = Node(
            interface=utility.Function(
                input_names=['trf_first', 'trf_second'],
                output_names=['trflist'],
                function=lambda trf_first, trf_second: [trf_first, trf_second]
            ), name="collect_trf"
        )
        wf.connect(bbr2ants, 'itk_transform', transform_list, 'trf_second')
        wf.connect('inputspec', 'nonlinear_reg_mtrx', transform_list, 'trf_first')

        applywarp = Node(interface=ants.ApplyTransforms(interpolation=interp, input_image_type=3), name='applywarp')
        wf.connect(transform_list, 'trflist', applywarp, 'transforms')
        wf.connect('inputspec', 'func', applywarp, 'input_image')
        wf.connect('inputspec', 'reference_brain', applywarp, 'reference_image')
    else:
        raise ValueError(f'%s is not a valid option for stdreg! Please choose \'fsl\' or \'ants\'!' % stdreg)

    if func_is_3D:
        qc_func2std = qc('qc_' + wf.name)
        if stdreg == 'fsl':
            wf.connect(applywarp, 'out_file', qc_func2std, 'func')
        elif stdreg == 'ants':
            wf.connect(applywarp, 'output_image', qc_func2std, 'func')
        wf.connect('inputspec', 'reference_brain', qc_func2std, 'overlay')

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
                                'example_func'],
              outputspec_fields=['out_file'])
def atlas2func(wf, stdreg='ants', interp="NearestNeighbor", **kwargs):
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
           out_file (str):

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

    qc_atlas2func = qc('qc_' + wf.name)
    if stdreg == 'fsl':
        wf.connect(applywarp, 'out_file', qc_atlas2func, 'func')#wf.connect(applywarp, 'out_file', qc_atlas2func, 'overlay')
    elif stdreg == 'ants':
        wf.connect(applywarp, 'output_image', qc_atlas2func, 'func')
    wf.connect('inputspec', 'example_func', qc_atlas2func, 'overlay')

    # Output
    if stdreg == 'fsl':
        wf.connect(applywarp, 'out_file', 'outputspec', 'out_file')
    elif stdreg == 'ants':
        wf.connect(applywarp, 'output_image', 'outputspec', 'out_file')

    # Sinking
    if stdreg == 'fsl':
        wf.connect(applywarp, 'out_file', 'sinker', 'atlas2func')
    elif stdreg == 'ants':
        wf.connect(applywarp, 'output_image', 'sinker', 'atlas2func')

