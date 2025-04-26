def scale_vol(in_file):
    import nibabel as nb
    import numpy as np
    import os

    img = nb.load(in_file)
    data = img.get_fdata()
    std = np.std(data, axis=3)
    std[std == 0] = 1  # divide with 1
    mean = np.mean(data, axis=3)

    for i in range(data.shape[3]):
        data[:, :, :, i] = (data[:, :, :, i] - mean) / std

    ret = nb.Nifti1Image(data, img.affine, img.header)
    out_file = "scaled_func.nii.gz"
    nb.save(ret, out_file)
    return os.path.join(os.getcwd(), out_file)


def scrub_image(scrub_input):
    """

    Method to run 3dcalc in order to scrub the image. This is used instead of
    the Nipype interface for 3dcalc because functionality is needed for
    specifying an input file with specifically-selected volumes.
    For example: input.nii.gz[2,3,4,..98], etc.

    Parameters:
        scrub_input (str): path to 4D file to be scrubbed, plus with selected volumes to be included

    Returns:
        scrubbed_image (str): path to the scrubbed 4D file
    """

    import os

    # input for 3dCalc looks like 4dfile.nii.gz[0,1,2,..100]
    # but the output of the scrubbing wf should look like 4dfile_scrubbed.nii.gz

    old_filename = os.path.basename(scrub_input)
    # e. g. sub-001_task-rest_bold_reoriented_masked_mcf_despike_regfilt_bp.nii.gz

    if '.nii.gz' in old_filename:
        ext_type = '.nii.gz'
    elif '.nii' in old_filename:
        ext_type = '.nii'
    else:
        raise ValueError(f'%s must have .nii or .nii.gz extension' % scrub_input)

    new_filename = old_filename[:old_filename.find(ext_type)] + '_scrubbed' + ext_type
    # e. g. sub-001_task-rest_bold_reoriented_masked_mcf_despike_regfilt_bp_scrubbed.nii.gz

    os.system(f"3dcalc -a %s -expr 'a' -prefix %s" % (scrub_input, new_filename))
    scrubbed_image = os.path.join(os.getcwd(), new_filename)

    return scrubbed_image


def registration_ants_hardcoded(brain, reference_brain, head, reference_head):

    """
    Todo Docs
    """

    import os
    import subprocess
    # parameters based on Satra's post: https://gist.github.com/satra/8439778
    regcmd = ["antsRegistration",
              "--collapse-output-transforms", "1",
              "--dimensionality", "3",

              "--initial-moving-transform",
              "[{0},{1},1]".format(reference_brain, brain),
              "--interpolation", "Linear",
              "--output", "[transform,transform_Warped.nii.gz]",

              "--transform", "Rigid[0.1]",
              "--metric", "MI[{0},{1},1,32," \
              "Regular,0.3]".format(reference_brain, brain),
              "--convergence", "[1000x500x250,1e-08,20]",
              "--smoothing-sigmas", "4.0x2.0x1.0",
              "--shrink-factors", "3x2x1",
              "--use-estimate-learning-rate-once", "1",
              "--use-histogram-matching", "0",

              "--transform", "Affine[0.1]",
              "--metric", "MI[{0},{1},1,32," \
              "Regular,0.3]".format(reference_brain, brain),
              "--convergence", "[1000x500x250,1e-08,20]",
              "--smoothing-sigmas", "4.0x2.0x1.0",
              "--shrink-factors", "3x2x1",
              "--use-estimate-learning-rate-once", "1",
              "--use-histogram-matching", "0",

              "--transform", "SyN[0.2,3.0,0.0]",
              "--metric", "Mattes[{0},{1},0.5,32]".format(reference_head, head),
              "--metric", "CC[{0},{1},0.5,4]".format(reference_head, head),
              "--convergence", "[100x50x30,-0.01,5]",
              "--smoothing-sigmas", "1.0x0.5x0.0",
              "--shrink-factors", "4x2x1",
              "--use-histogram-matching", "1",
              "--winsorize-image-intensities", "[0.005,0.995]",
              "--use-estimate-learning-rate-once", "1",
              "--write-composite-transform", "1"]

    try:
        output = subprocess.check_output(regcmd)
    except Exception as e:
        raise Exception(
            '[!] ANTS registration did not complete successfully!\n\nError details:\n{0}\n\n'.format(e)
        )

    transform_composite = None
    transform_inverse_composite = None
    warped_image = None

    files = [f for f in os.listdir('.') if os.path.isfile(f)]

    for f in files:
        if ("transformComposite" in f) and ("Warped" not in f):
            transform_composite = os.getcwd() + "/" + f
        if ("transformInverseComposite" in f) and ("Warped" not in f):
            transform_inverse_composite = os.getcwd() + "/" + f
        if "Warped" in f:
            warped_image = os.getcwd() + "/" + f

    if not warped_image:
        raise Exception(
            '[!] No registration output file found. ANTS registration may not have completed successfully.\n\n'
        )

    return transform_composite, transform_inverse_composite, warped_image
