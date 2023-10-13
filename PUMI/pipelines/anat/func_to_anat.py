from nipype.interfaces.utility import Function
from PUMI.engine import NestedNode as Node, AnatPipeline, QcPipeline
from PUMI.pipelines.multimodal.image_manipulation import pick_volume, vol2png
from nipype.interfaces import fsl


@QcPipeline(inputspec_fields=['func2anat', 'wm_bb_mask'],
            outputspec_fields=['out_file'])
def func2anat_qc(wf, **kwargs):
    """

    Create and save quality check image for func2anat workflow

    Inputs:
        func2anat (str): path to out_file of func2anat workflow
        wm_bb_mask (str): white matter mask calculated in func2anat workflow

    Outputs:
        out_file (str): path to quality check image

    Sinking
        func2anat quality check image

    """

    # Create png images for quality check
    func2anat_vol2png = vol2png('func2anat_vol2png')
    wf.connect('inputspec', 'func2anat', func2anat_vol2png, 'bg_image')
    wf.connect('inputspec', 'wm_bb_mask', func2anat_vol2png, 'overlay_image')

    wf.connect(func2anat_vol2png, 'out_file', 'sinker', 'qc_func2anat')



@AnatPipeline(inputspec_fields=['func', 'head', 'anat_wm_segmentation', 'anat_gm_segmentation',
                                'anat_csf_segmentation', 'anat_ventricle_segmentation'],
              outputspec_fields=['func_sample2anat', 'example_func', 'func_to_anat_linear_xfm',
                                 'anat_to_func_linear_xfm', 'csf_mask_in_funcspace', 'csf_mask_in_funcspace',
                                 'csf_mask_in_funcspace', 'ventricle_mask_in_funcspace', 'wm_mask_in_funcspace',
                                 'gm_mask_in_funcspace'])
def func2anat(wf, func_volume='middle', bbr=True, **kwargs):
        """

        Registration of functional image to anat.

        Parameters:
            func_volume: Select which volume from the functional image should be used.
                         Can be either 'first', 'middle', 'last', 'mean' or a number.
            bbr (bool): If True (default), BBR registration is used. If False, linear registration is used.

        Inputs:
            func (str): Functional image
            (The one which is the closest to the fieldmap recording in time should be chosen
            e.g: if fieldmap was recorded after the fMRI the last volume of it should be chosen)
            head (str): The oriented T1w image.
            anat_wm_segmentation (str): WM probability mask
            anat_gm_segmentation (str): GM probability mask
            anat_csf_segmentation (str): CSF probability mask

        Acknowledgements:
            Adapted from Balint Kincses (2018) code.
            Modified version of CPAC.registration.registration
            (https://github.com/FCP-INDI/C-PAC/blob/main/CPAC/registration/registration.py)

        """

        myonevol = pick_volume('myonevol', volume=func_volume)
        wf.connect('inputspec', 'func', myonevol, 'in_file')

        # trilinear interpolation is used by default in linear registration for func to anat
        linear_func_to_anat = Node(interface=fsl.FLIRT(), name='linear_func_to_anat')
        linear_func_to_anat.inputs.cost = 'corratio'
        linear_func_to_anat.inputs.dof = 6
        linear_func_to_anat.inputs.out_matrix_file = "lin_mat"
        wf.connect(myonevol, 'out_file', linear_func_to_anat, 'in_file')
        wf.connect('inputspec', 'head', linear_func_to_anat, 'reference')

        # WM probability map is thresholded and masked
        wm_bb_mask = Node(interface=fsl.ImageMaths(), name='wm_bb_mask')
        wm_bb_mask.inputs.op_string = '-thr 0.5 -bin'
        wf.connect('inputspec', 'anat_wm_segmentation', wm_bb_mask, 'in_file')

        # CSf probability map is thresholded and masked
        csf_bb_mask = Node(interface=fsl.ImageMaths(), name='csf_bb_mask')
        csf_bb_mask.inputs.op_string = '-thr 0.5 -bin'
        wf.connect('inputspec', 'anat_csf_segmentation', csf_bb_mask, 'in_file')

        # GM probability map is thresholded and masked
        gm_bb_mask = Node(interface=fsl.ImageMaths(), name='gm_bb_mask')
        gm_bb_mask.inputs.op_string = '-thr 0.1 -bin'  # liberal mask to capture all gm signal
        wf.connect('inputspec', 'anat_gm_segmentation', gm_bb_mask, 'in_file')

        # ventricle probability map is thresholded and masked
        vent_bb_mask = Node(interface=fsl.ImageMaths(), name='vent_bb_mask')
        vent_bb_mask.inputs.op_string = '-thr 0.8 -bin -ero -dilM'  # stricter threshold and some morphology for compcor
        wf.connect('inputspec', 'anat_ventricle_segmentation', vent_bb_mask, 'in_file')

        if bbr:
            def bbreg_args(bbreg_target):
                """

                A function is defined for define bbr argument which says flirt to perform bbr registration
                for each element of the list, due to MapNode

                Parameter:

                """

                return '-cost bbr -wmseg ' + bbreg_target

            bbreg_arg_convert = Node(interface=Function(input_names=["bbreg_target"],
                                                        output_names=["arg"],
                                                        function=bbreg_args),
                                     name="bbr_arg_converter")
            wf.connect('inputspec', 'anat_wm_segmentation', bbreg_arg_convert, 'bbreg_target')

            # BBR registration within the FLIRT node
            bbreg_func_to_anat = Node(interface=fsl.FLIRT(), name='bbreg_func_to_anat')
            bbreg_func_to_anat.inputs.dof = 6
            wf.connect(linear_func_to_anat, 'out_matrix_file', bbreg_func_to_anat, 'in_matrix_file')
            wf.connect(myonevol, 'out_file', bbreg_func_to_anat, 'in_file')
            wf.connect(bbreg_arg_convert, 'arg', bbreg_func_to_anat, 'args')
            wf.connect('inputspec', 'head', bbreg_func_to_anat, 'reference')

            main_func2anat = bbreg_func_to_anat
        else:
            main_func2anat = linear_func_to_anat

        # calculate the inverse of the transformation matrix (of func to anat)
        convertmatrix = Node(interface=fsl.ConvertXFM(), name="convertmatrix")
        convertmatrix.inputs.invert_xfm = True
        wf.connect(main_func2anat, 'out_matrix_file', convertmatrix, 'in_file')

        # use the invers registration (anat to func) to transform anatomical csf mask
        reg_anatmask_to_func1 = Node(interface=fsl.FLIRT(apply_xfm=True, interp='nearestneighbour'),
                                     name='anatmasks_to_func1')
        wf.connect(convertmatrix, 'out_file', reg_anatmask_to_func1, 'in_matrix_file')
        wf.connect(myonevol, 'out_file', reg_anatmask_to_func1, 'reference')
        wf.connect(csf_bb_mask, 'out_file', reg_anatmask_to_func1, 'in_file')

        # use the invers registration (anat to func) to transform anatomical wm mask
        reg_anatmask_to_func2 = Node(interface=fsl.FLIRT(apply_xfm=True, interp='nearestneighbour'),
                                     name='anatmasks_to_func2')
        wf.connect(convertmatrix, 'out_file', reg_anatmask_to_func2, 'in_matrix_file')
        wf.connect(myonevol, 'out_file', reg_anatmask_to_func2, 'reference')
        wf.connect(wm_bb_mask, 'out_file', reg_anatmask_to_func2, 'in_file')

        # use the invers registration (anat to func) to transform anatomical gm mask
        reg_anatmask_to_func3 = Node(interface=fsl.FLIRT(apply_xfm=True, interp='nearestneighbour'),
                                     name='anatmasks_to_func3')
        wf.connect(convertmatrix, 'out_file', reg_anatmask_to_func3, 'in_matrix_file')
        wf.connect(myonevol, 'out_file', reg_anatmask_to_func3, 'reference')
        wf.connect(gm_bb_mask, 'out_file', reg_anatmask_to_func3, 'in_file')

        # use the invers registration (anat to func) to transform anatomical gm mask
        reg_anatmask_to_func4 = Node(interface=fsl.FLIRT(apply_xfm=True, interp='nearestneighbour'),
                                     name='anatmasks_to_func4')
        wf.connect(convertmatrix, 'out_file', reg_anatmask_to_func4, 'in_matrix_file')
        wf.connect(myonevol, 'out_file', reg_anatmask_to_func4, 'reference')
        wf.connect(vent_bb_mask, 'out_file', reg_anatmask_to_func4, 'in_file')

        qc_func2anat = func2anat_qc('qc_func2anat')
        wf.connect(main_func2anat, 'out_file', qc_func2anat, 'func2anat')
        wf.connect(wm_bb_mask, 'out_file', qc_func2anat, 'wm_bb_mask')

        # sink the results
        wf.connect(main_func2anat, 'out_file', 'sinker', "func2anat_qc")
        wf.connect(main_func2anat, 'out_matrix_file', 'sinker', 'func_to_anat_linear_xfm')
        wf.connect(convertmatrix, 'out_file', 'sinker', 'anat_to_func_linear_xfm')



        # outputspec
        wf.connect(myonevol, 'out_file', 'outputspec', 'example_func')
        wf.connect(reg_anatmask_to_func1, 'out_file', 'outputspec', 'csf_mask_in_funcspace')
        wf.connect(reg_anatmask_to_func2, 'out_file', 'outputspec', 'wm_mask_in_funcspace')
        wf.connect(reg_anatmask_to_func3, 'out_file', 'outputspec', 'gm_mask_in_funcspace')
        wf.connect(reg_anatmask_to_func4, 'out_file', 'outputspec', 'ventricle_mask_in_funcspace')
        wf.connect(main_func2anat, 'out_file', 'outputspec', 'func_sample2anat')
        wf.connect(main_func2anat, 'out_matrix_file', 'outputspec', 'func_to_anat_linear_xfm')
        wf.connect(convertmatrix, 'out_file', 'outputspec', 'anat_to_func_linear_xfm')
