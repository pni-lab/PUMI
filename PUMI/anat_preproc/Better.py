def bet_workflow(Robust=True, fmri=False, SinkTag="anat_preproc", wf_name="brain_extraction"):
    """

    Creates a brain extracted image and its mask from a T1w anatomical image.

    :param bool Robust: Perform robust brain centre estimation (iterates BET several times)?
    :param bool fmri: Input from an fMRI?
    :param str SinkTag: Output directory in which the results can be found.
    :param str wf_name: Name of the workflow.
    :return: bet workflow

    **workflow inputs**:

    - in_file (str) - The reoriented anatomical file.
    - [optional] fract_int_thr (float) - FSL BET fractional intensity threshold.
    - [optional] vertical_gradient (float) - FSL BET vertical gradient in fractional intensity threshold.

    **workflow outputs**:

    - brain (str) - Path to resulting extracted brain.
    - brain-mask (str) - Path to binary brain mask.

    Modified version of CPAC.anat_preproc.anat_preproc
    (https://github.com/FCP-INDI/C-PAC/blob/master/CPAC/anat_preproc/anat_preproc.py)
    and Balint Kincses (2018) code.

    """

    import os
    import nipype
    import nipype.pipeline as pe
    import nipype.interfaces.utility as utility
    import nipype.interfaces.fsl as fsl
    import nipype.interfaces.io as io
    import PUMI.utils.QC as qc
    import PUMI.utils.default as default
    import PUMI.func_preproc.Onevol as onevol

    SinkDir = os.path.abspath(default._SinkDir_ + "/" + SinkTag)
    if not os.path.exists(SinkDir):
        os.makedirs(SinkDir)

    # Basic interface class generates identity mappings
    inputspec = pe.Node(
        utility.IdentityInterface(
            fields=[
                'in_file',
                'opt_R',
                'fract_int_thr',  # optional
                'vertical_gradient'  # optional
                ]
        ),
        name='inputspec'
    )
    inputspec.inputs.opt_R = Robust
    if fmri:
        inputspec.inputs.fract_int_thr = default._fsl_bet_fract_int_thr_func_
    else:
        inputspec.inputs.fract_int_thr = default._fsl_bet_fract_int_thr_anat_

    inputspec.inputs.vertical_gradient = default._fsl_bet_vertical_gradient_

    # Wraps command **bet**
    bet = pe.Node(interface=fsl.BET(), name='bet')
    bet.inputs.mask = True
    if fmri:
        bet.inputs.functional = True
        myonevol = onevol.onevol_workflow(wf_name="onevol")
        applymask = pe.Node(fsl.ApplyMask(), name="apply_mask")

    myqc = qc.vol2png(wf_name, overlay=True)

    # Basic interface class generates identity mappings
    outputspec = pe.Node(
        utility.IdentityInterface(
            fields=[
                'brain',
                'brain_mask'
                ]
        ),
        name='outputspec'
    )

    # Save outputs which are important
    ds = pe.Node(interface=io.DataSink(), name='ds')
    ds.inputs.base_directory = SinkDir
    ds.inputs.regexp_substitutions = [("(\/)[^\/]*$", ".nii.gz")]

    # Create a workflow to connect all those nodes
    analysisflow = nipype.Workflow(wf_name)  # The name here determine the folder of the workspace
    analysisflow.base_dir = '.'
    analysisflow.connect([(inputspec, bet, [('in_file', 'in_file'),
                                            ('opt_R', 'robust'),
                                            ('fract_int_thr', 'frac'),
                                            ('vertical_gradient', 'vertical_gradient')
                                            ]),
                          (bet, outputspec, [('mask_file', 'brain_mask')])
                          ])
    if fmri:
        analysisflow.connect([(bet, myonevol, [('mask_file', 'inputspec.func')]),
                              (myonevol, applymask, [('outputspec.func1vol', 'mask_file')]),
                              (inputspec, applymask, [('in_file', 'in_file')]),
                              (applymask, outputspec, [('out_file', 'brain')])
                              ])
    else:
        analysisflow.connect(bet, 'out_file', outputspec, 'brain')
    analysisflow.connect([(bet, ds, [('out_file', 'bet_brain'),
                                     ('mask_file', 'brain_mask')
                                     ]),
                          (inputspec, myqc, [('in_file', 'inputspec.bg_image')]),
                          (bet, myqc, [('out_file', 'inputspec.overlay_image')])
                          ])
    return analysisflow
