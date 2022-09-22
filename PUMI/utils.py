from templateflow import api as tflow
import os


def get_config(wf, section, config):
    """
    Return the absolute path to the desired config file.

    The method is going to search for a specified path in the settings.ini.
    If no path was specified, a fallback value is used if possible.

    Note:
    Unlike some other methods, in the case of a relative path the path is NOT considered relative to the FSL-Dir,
    but relative to the current working directory!

    Parameters:
        wf (Workflow): the workflow
        section (str): the section where the path should be found in settings.ini (e.g. 'FSL')
        config (str): name (key) of the config (e.g. 'fnirt_config')
    """
    path = wf.cfg_parser.get(section, config, fallback='')
    if path == '':  # provide fallback values
        if config == 'fnirt_config':
            return os.path.join(os.environ['FSLDIR'], 'etc/flirtsch/TI_2_MNI152_2mm.cnf')
        else:
            raise ValueError(
                f"""
                    Can't find a path or fallback value for the config '%s' in the section '%s' in the settings.ini.
                    Please specify a path for the config in the settings.ini!
                """ % (config, section)
            )

    if path.startswith('/'):
        return path
    else:
        return os.path.join(os.getcwd(), path)


def get_reference(wf, type, ref=None):
    """
    Returns the absolute path to the desired reference.
    Possible values for the type parameter are 'head', 'brain', 'brain_mask' or 'ventricle_mask'.

    If ref = None, the method looks in the settings.ini for specified paths (and source specifications) for the desired reference in
    the TEMPLATES section.

    If no path was specified, the respective 2mm reference from FSL's standard repertoire is returned.
    If a path was specified, it looks if also a source was specified.
    If no source was specified (or the source is 'local'), then it's going to search local.
    If a local search is performed, it is checked if the path starts with a '/'. If so, this path is considered as
    an absolute path, otherwise the path is considered relative to the FSL-Dir (NOT the current working directory)!
    If the source is 'templateflow' or also 'tf', it is tried to get the reference from templateflow.

    Some possible path specification without use of templateflow:
    'head = data/standard/MNI152_T1_2mm.nii.gz' or
    'head = data/standard/MNI152_T1_2mm.nii.gz; source=local' or
    'head = /usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz'

    Possible path specification with use of templateflow:
    'head = tpl-MNI152Lin/tpl-MNI152Lin_res-02_T1w.nii.gz; source=templateflow'

    The 'tpl-' in the folder/template specification (NOT the file specification!) can also be omitted.
    Also 'tf' can be used as abbreviation for templateflow.

    So this is also okay:
    'head = MNI152Lin/tpl-MNI152Lin_res-02_T1w.nii.gz; source=tf'

    Be aware that 'head', 'brain' and 'brain_mask' must also be lowercased in the settings.ini!
    """
    if type not in ['head', 'brain', 'brain_mask', 'ventricle_mask']:
        raise ValueError('Can only provide references for \'head\', \'brain\', \'brain_mask\', \'ventricle_mask\'')

    if ref is None:
        query = wf.cfg_parser.get('TEMPLATES', type, fallback='')
        query = query.replace(' ', '')
    else:
        query = ref

    div = len(query.split(';source='))
    if div == 1:  # no occurrence of ';source=' (no source specification) -> search locally
        return get_ref_locally(wf, type)
    elif div == 2:  # one occurrence of ';source=' (source was specified) -> look at the specification
        path, source = query.split(';source=')
        if source == 'local':
            return get_ref_locally(wf, type)
        elif source == 'templateflow' or source == 'tf':
            return get_ref_from_templateflow(path)
        else:  # No valid source was provided
            raise ValueError(
                f'Source can be \'local\' or \'templateflow\' (\'tf\'). %s is not a valid option!' % source
            )
    else:  # more than one occurrence of ';source='
        raise ValueError(
            f'Check your settings.ini! Your path for %s contains the more than one source specification' % ref
        )


def get_ref_from_templateflow(query):
    """
    Try to get the specified reference from templateflow and return the absolute path to the file.
    The schema for the query is 'template/file'.
    Note: 'tpl-' in the template specification (NOT the file specification!) can be omitted.
    Look at the available references at 'https://www.templateflow.org/browse/'

    A possible query would be: 'tpl-MNI152Lin/tpl-MNI152Lin_res-02_T1w.nii.gz'
    Also okay: 'MNI152Lin/tpl-MNI152Lin_res-02_T1w.nii.gz'
    """
    path = query
    if path.startswith('/'):
        path = path.replace('/', '', 1)
    if path.startswith('tpl-'):
        path = path.replace('tpl-', '', 1)

    if len(path.split('/')) != 2:
        raise ValueError(
            f'Illegal schema. Please provide your query in the form template/file and not %s' % query
        )

    template_dir, template_file = path.split('/')
    search_result = list(map(os.path.abspath, list(tflow.get(template_dir))))

    template_in_result = [template_file in path for path in search_result]
    if any(template_in_result):
        return search_result[template_in_result.index(True)]
    else:
        raise Exception(
            f'Could not find the specified file. Are you sure %s is available in the templateflow archive?' % query
        )


def get_ref_locally(wf, ref):
    """
    Try to get the reference locally and return the absolute path to the file
    Possible values for the ref parameter are 'head', 'brain', 'brain_mask' or 'ventricle_mask'.

    The method looks in the settings.ini for specified paths for the desired reference in the TEMPLATES section.

    If no path was specified, the respective 2mm reference from FSL's standard repertoire is returned.
    If a path was specified, it is checked if the path starts with a '/'. If so, this path is considered as
    an absolute path, otherwise the path is considered relative to the FSL-Dir (NOT the current working directory)!
    """
    if ref not in ['head', 'brain', 'brain_mask', 'ventricle_mask']:
        raise ValueError('Can only provide references for \'head\', \'brain\', \'brain_mask\', \'ventricle_mask\'')

    path = wf.cfg_parser.get('TEMPLATES', ref, fallback='')

    if path == '':  # provide fallback values
        if ref == 'head':
            return os.path.join(os.environ['FSLDIR'], 'data/standard/MNI152_T1_2mm.nii.gz')
        elif ref == 'brain':
            return os.path.join(os.environ['FSLDIR'], 'data/standard/MNI152_T1_2mm_brain.nii.gz')
        else:
            return os.path.join(os.environ['FSLDIR'], 'data/standard/MNI152_T1_2mm_brain_mask_dil.nii.gz')

    if path.startswith('/'):  # absolute path
        return path
    else:  # relative path to the FSL-Dir
        return os.path.join(os.environ['FSLDIR'], path)


def plot_roi(roi_img, bg_img=None, cut_coords=5, output_file=None, display_mode='mosaic', figure=None, axes=None,
             title=None, annotate=True, draw_cross=True, black_bg=True, threshold=0.5, alpha=0.7,
             cmap='tab10', dim='auto', vmin=None, vmax=None, resampling_interpolation='nearest', view_type='continuous',
             linewidths=2.5, colorbar=False, save_img=True, **kwargs):
    """

    Wrapper for nilearn's plot_roi method (with small modifications).

    Can be used in a nipype function node. In this case output_file should stay None and save_img should stay True!

    Parameters:
        Only parameter that does not occur in nilearn's plot_roi method is save_img.
        Set to False if you don't want to save the result and just need the plot object.
        This parameter is necessary because we substitute output_file by the current working directory and a suitable
        filename if output_file is set to None (default).
        In case the function is executed within a nipype function node, the current working directory is the working
        directory of the respective node.
        We introduced this modifications in order to be able to use this method easily in nipype function nodes.

    For more information about the other parameters, see the documentation of nilearn.
    https://nilearn.github.io/modules/generated/nilearn.plotting.plot_roi.html

    Only a few changes have been made to the default parameters.
    Here a mosaic plot with 5 columns is generated by default, the background of every plot is black and the default
    cmap has been changed.

    Returns:
        plot (nilearn.plotting.displays.OrthoSlicer): Plot object.
        output_file (str): Path to the saved plot (if save_img is False, None is returned).

    Acknowledgements:
        Further informations:
            - https://nilearn.github.io/index.html

    """
    from nilearn import plotting
    import os

    if save_img:
        if output_file is None:
            roi_img_name = roi_img.split('/')[-1].split('.')[0]
            output_file = os.path.join(os.getcwd(), roi_img_name + '_plot.png')
        else:
            if not output_file.startswith('/'):
                output_file = os.path.join(os.getcwd(), output_file)
    else:
        output_file = None  # make sure that no file is created when save_img=False

    plot = plotting.plot_roi(roi_img, bg_img=bg_img, cut_coords=cut_coords, output_file=output_file,
                             display_mode=display_mode, figure=figure, axes=axes, title=title, annotate=annotate,
                             draw_cross=draw_cross,
                             black_bg=black_bg, threshold=threshold, alpha=alpha, cmap=cmap, dim=dim, vmin=vmin,
                             vmax=vmax, resampling_interpolation=resampling_interpolation, view_type=view_type,
                             linewidths=linewidths, colorbar=colorbar, **kwargs)

    return plot, output_file


def create_segmentation_qc(overlay, bg_img=None, output_file=None, cut_coords=5, cmap='winter', **kwargs):
    """

    Create segmentation (e.g. brain extraction, tissue segmentation) quality check images.

    Can be used in a nipype function node. In this case output_file should stay None!

    Parameters:
        overlay (str): Path to the overlay (e.g. in brain extraction workflows the extracted brain).
        bg_img (str): Path to the background (e.g. in brain extraction workflows the head).
        output_file (str): Filename of quality check image. Can be be an absolute path or a relative path.
                           If it's set to None (default), the filename is automatically generated.
        cmap (matplotlib colormap): Colormap.
        **kwargs: These parameters are passed to the plot_roi method.

    Returns:
        output_file (str): Path to the saved plot.

    """
    from PUMI.utils import plot_roi

    plot, output_file = plot_roi(roi_img=overlay, bg_img=bg_img, output_file=output_file, cut_coords=cut_coords,
                                 cmap=cmap, **kwargs)
    return output_file


def create_coregistration_qc(registered_brain, template, output_file=None, levels=None, cmap='winter', **kwargs):
    """

    Create coregistration quality check images.

    Can be used in a nipype function node. In this case output_file should stay None!

    Parameters
    ----------
    registered_brain (str): Path to the registered brain.
    template (str): Path to the used template (reference) file.
    output_file (str): Filename of quality check image. Can be be an absolute path or a relative path.
                       If it's set to None (default), the path and filename is automatically generated.
    levels (list): Contour fillings levels. If set to None, [0.5] will be used.
    cmap (matplotlib colormap): Colormap.
    **kwargs: These parameters are passed to plot_roi method.

    Returns
    ----------
    output_file (str): Path to the saved plot.

    """
    from PUMI.utils import plot_roi
    import os

    if levels is None:
        levels = [0.5]

    plot, _ = plot_roi(roi_img=registered_brain, bg_img=template, cmap=cmap, alpha=0, save_img=False, **kwargs)
    plot.add_contours(registered_brain, levels=levels, colors='r')

    if output_file is None:
        registered_brain_filename = registered_brain.split('/')[-1].split('.')[0]
        output_file = os.path.join(os.getcwd(), registered_brain_filename + '_plot.png')
    else:
        if not output_file.startswith('/'):
            output_file = os.path.join(os.getcwd(), output_file)
    plot.savefig(output_file)

    return output_file


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


def scale_vol(in_file):
    import nibabel as nb
    import numpy as np
    import os

    img = nb.load(in_file)
    data = img.get_data()
    std = np.std(data, axis=3)
    std[std == 0] = 1  # divide with 1
    mean = np.mean(data, axis=3)

    for i in range(data.shape[3]):
        data[:, :, :, i] = (data[:, :, :, i] - mean) / std

    ret = nb.Nifti1Image(data, img.affine, img.header)
    out_file = "scaled_func.nii.gz"
    nb.save(ret, out_file)
    return os.path.join(os.getcwd(), out_file)


def drop_first_line(in_file):
    import os

    with open(in_file, 'r') as fin:
        data = fin.read().splitlines(True)

    fname = os.path.split(in_file)[-1]
    with open(fname, 'w') as fout:
        fout.writelines(data[1:])  # don't write the first line into the new file
        return os.path.join(os.getcwd(), fname)


def calc_friston_twenty_four(in_file):
    """

    Method to calculate friston twenty-four parameters

    Parameters:
        in_file (str): input movement parameters file from motion correction

    Returns:
        new_file (str): output 1D file containing 24 parameter values

    """

    import numpy as np
    import os

    data = np.genfromtxt(in_file)
    data_squared = data ** 2
    new_data = np.concatenate((data, data_squared), axis=1)
    data_roll = np.roll(data, 1, axis=0)
    data_roll[0] = 0
    new_data = np.concatenate((new_data, data_roll), axis=1)
    data_roll_squared = data_roll ** 2
    new_data = np.concatenate((new_data, data_roll_squared), axis=1)
    new_file = os.path.join(os.getcwd(), 'fristons_twenty_four.1D')
    np.savetxt(new_file, new_data, delimiter=' ')
    return new_file


def calculate_FD_Jenkinson(in_file):
    """

    Method to calculate friston twenty four parameters

    Parameters:
        in_file (str): input movement parameters file from motion correction

    Returns:
        new_file (str): path to output file

    """

    import numpy as np
    import os
    import math

    out_file = os.path.join(os.getcwd(), 'FD_J.1D')

    lines = open(in_file, 'r').readlines()
    rows = [[float(x) for x in line.split()] for line in lines]
    cols = np.array([list(col) for col in zip(*rows)])

    translations = np.transpose(np.diff(cols[3:6, :]))
    rotations = np.transpose(np.diff(cols[0:3, :]))

    flag = 0
    rmax = 80.0  # The default radius (as in FSL) of a sphere represents the brain

    out_lines = []

    for i in range(0, translations.shape[0] + 1):

        if flag == 0:
            flag = 1
            # first timepoint
            out_lines.append('0')
        else:
            r = rotations[i - 1,]
            t = translations[i - 1,]
            FD_J = math.sqrt((rmax * rmax / 5) * np.dot(r, r) + np.dot(t, t))
            out_lines.append('\n{0:.8f}'.format(FD_J))

    with open(out_file, "w") as f:
        for line in out_lines:
            f.write(line)
    return out_file


def mean_from_txt(in_file, axis=None, header=False, out_file='mean.txt'):
    """

    Calculate column-means, row-means or the global mean depending on the 'axis' parameter and save it to
    another text-file.

    Caution: Name in the old PUMI was txt2MeanTxt

    Parameters:
        in_file (str): input file
        axis (None/int/(int,int)): axis or axes along which the means are computed.
                                   Default: Compute mean of the flattened array.
        header (bool): Drop line if True
        out_file (str): Name of the resulting text-file. If only the filename is given, it will be saved into the
                        current working directory.

    Returns:
        new_file (str): path to new file

    """
    import numpy as np
    import os

    if header:
        print("drop first line")
        data = np.loadtxt(in_file, skiprows=1)
    else:
        print("don't drop first line")
        data = np.loadtxt(in_file)
    mean = data.mean(axis=axis)
    np.savetxt(out_file, [mean])
    if out_file.startswith('/'):
        new_file = out_file
    else:
        new_file = os.path.join(os.getcwd(), out_file)  # need to add '/' manually?
    return new_file


def max_from_txt(in_file, axis=None, header=False, out_file='max.txt'):
    """

    Saves the maximum along a given axis into another text-file.

    Caution: Name in the old PUMI was txt2MaxTxt

    Parameters:
        in_file (str): input file
        axis (None/int/(int,int)): axis or axes along the maximum values are computed.
                                   Default: Use flattened array.
        header (bool): Drop line if True
        out_file (str): Name of the resulting text-file. If only the filename is given, it will be saved into the
                        current working directory.

    Returns:
        new_file (str): path to new file

    """
    import numpy as np
    import os

    if header:
        print("drop first line")
        data = np.loadtxt(in_file, skiprows=1)
    else:
        print("don't drop first line")
        data = np.loadtxt(in_file)
    dmax = data.max(axis=axis)
    np.savetxt(out_file, [dmax])
    if out_file.startswith('/'):
        new_file = out_file
    else:
        new_file = os.path.join(os.getcwd(), out_file)  # need to add '/' manually?
    return new_file


def get_indx(scrub_input, frames_in_1D_file):
    """

    Method to get the list of time
    frames that are to be included

    Parameters:
        in_file (str): path to file containing the valid time frames

    Returns:
        scrub_input_string (str): input string for 3dCalc in scrubbing workflow,
                              looks something like " 4dfile.nii.gz[0,1,2,..100] "
    """

    frames_in_idx_str = '[' + ','.join(str(x) for x in frames_in_1D_file) + ']'
    scrub_input_string = scrub_input + frames_in_idx_str

    return scrub_input_string


def scrub_image(scrub_input):
    """

    Method to run 3dcalc in order to scrub the image. This is used instead of
    the Nipype interface for 3dcalc because functionality is needed for
    specifying an input file with specifically-selected volumes. For example:
        input.nii.gz[2,3,4,..98], etc.

    Parameters:
        scrub_input (str): path to 4D file to be scrubbed, plus with selected volumes to be included

    Returns:
        scrubbed_image (str): path to the scrubbed 4D file
    """

    import os

    os.system("3dcalc -a %s -expr 'a' -prefix scrubbed_preprocessed.nii.gz" % scrub_input)

    scrubbed_image = os.path.join(os.getcwd(), "scrubbed_preprocessed.nii.gz")

    return scrubbed_image


def above_threshold(in_file, threshold=0.2, frames_before=1, frames_after=2):

    """

        todo docs

    """

    import os
    import numpy as np
    from numpy import loadtxt, savetxt

    powersFD_data = loadtxt(in_file, skiprows=1)
    np.insert(powersFD_data, 0, 0)  # TODO_ready: why do we need this: see output of nipype.algorithms.confounds.FramewiseDisplacement
    frames_in_idx = np.argwhere(powersFD_data < threshold)[:, 0]
    frames_out = np.argwhere(powersFD_data >= threshold)[:, 0]

    extra_indices = []
    for i in frames_out:

        # remove preceding frames
        if i > 0:
            count = 1
            while count <= frames_before:
                extra_indices.append(i - count)
                count += 1

        # remove following frames
        count = 1
        while count <= frames_after:
            if i+count < len(powersFD_data):  # do not censor unexistent data
                extra_indices.append(i + count)
            count += 1
    indices_out = list(set(frames_out) | set(extra_indices))
    indices_out.sort()

    frames_out_idx = indices_out
    frames_in_idx = np.setdiff1d(frames_in_idx, indices_out)

    FD_scrubbed = powersFD_data[frames_in_idx]
    fd_scrubbed_file = os.path.join(os.getcwd(), 'FD_scrubbed.csv')
    savetxt(fd_scrubbed_file, FD_scrubbed, delimiter=",")

    frames_in_idx_str = ','.join(str(x) for x in frames_in_idx)
    frames_in_idx = frames_in_idx_str.split()

    percentFD = (len(frames_out_idx) * 100 / (len(powersFD_data) + 1)) # % of frames censored
    percent_scrubbed_file = os.path.join(os.getcwd(), 'percent_scrubbed.txt')
    f = open(percent_scrubbed_file, 'w')
    f.write("%.3f" % (percentFD))
    f.close()

    nvol = len(powersFD_data)

    return frames_in_idx, frames_out_idx, percentFD, percent_scrubbed_file, fd_scrubbed_file, nvol


def concatenate(fname='parfiles.txt', **pars):

    """

    todo Docs

    """
    import os
    import numpy as np

    par_files = list(pars.values())

    totpar = np.loadtxt(par_files[0])
    for idx in range(1, len(par_files)):
        if par_files[idx] is None:
            continue
        tmp = np.loadtxt(par_files[idx])
        totpar = np.concatenate((totpar, tmp), axis=1)
        if fname.startswith('/'):
            path = fname
        else:
            path = os.path.join(os.getcwd(), fname)
    np.savetxt(path, totpar)
    return path


def mist_modules(mist_directory, resolution="122"):
    """
       Return a list of the modules contained in the MIST atlas
       Parameters:
           mist_directory (str): Path to the MIST directory
           resolution (str): Resolution (you have to check which resolutions are valid)
       Returns:
           result ([str]): A list containing the modules in the MIST atlas
    """

    import pandas as pd

    resolution = 's' + resolution
    mist_hierarchy_filename = mist_directory + '/' + 'Hierarchy/MIST_PARCEL_ORDER_ROI.csv'
    mist_hierarchy = pd.read_csv(mist_hierarchy_filename, sep=",")
    mist_hierarchy_res = mist_hierarchy[(resolution)]
    mist_hierarchy_res = mist_hierarchy_res.drop_duplicates()

    modul_indices = mist_hierarchy.loc[mist_hierarchy_res.index.values, ['s7', resolution]].sort_values(by=resolution)['s7']
    mist_s7_filename = mist_directory + '/' + 'Parcel_Information/MIST_7.csv'
    mist_s7 = pd.read_csv(mist_s7_filename, sep=";")

    labels = mist_s7.loc[modul_indices-1, ['roi', 'label']].reset_index()
    result = labels['label'].values.tolist()
    return result


def mist_labels(mist_directory, resolution="122"):
    """
       Return a list of the labels contained in the MIST atlas
       Parameters:
           mist_directory (str): Path to the MIST directory
           resolution (str): Resolution (you have to check which resolutions are valid)
       Returns:
           result ([str]): A list containing the labels in the MIST atlas
    """

    import pandas as pd

    mist_filename = mist_directory + '/' + 'Parcel_Information/MIST_' + resolution + '.csv'

    mist = pd.read_csv(mist_filename, sep=";")
    result = mist['label'].values.tolist()
    return result


def relabel_atlas(atlas_file, modules, labels):
    """
       Relabel atlas
       * Beware : currently works only with labelmap!!
       Parameters:
           atlas_file(str): Path to the atlas file
           modules ([str]): List containing the modules in MIST
           labels ([str]): List containing the labels in MIST
       Returns:
           relabel_file (str): Path to relabeld atlas file
           reordered_modules ([str]): list containing reordered module names
           reordered_labels ([str]): list containing reordered label names
           new_labels (str): Path to .tsv-file with the new labels
    """

    import os
    import numpy as np
    import pandas as pd
    import nibabel as nib

    df = pd.DataFrame({'modules': modules, 'labels': labels})
    df.index += 1  # indexing from 1

    reordered = df.sort_values(by='modules')

    # relabel labelmap
    img = nib.load(atlas_file)
    if len(img.shape) != 3:
        raise Exception("relabeling does not work for probability maps!")

    lut = reordered.reset_index().sort_values(by="index").index.values + 1
    lut = np.array([0] + lut.tolist())
    # maybe this is a bit complicated, but believe me it does what it should

    data = img.get_data()
    newdata = lut[np.array(data, dtype=np.int32)]  # apply lookup table to swap labels

    img = nib.Nifti1Image(newdata.astype(np.float64), img.affine)
    nib.save(img, 'relabeled_atlas.nii.gz')

    out = reordered.reset_index()
    out.index = out.index + 1
    relabel_file = os.path.join(os.getcwd(), 'relabeled_atlas.nii.gz')
    reordered_modules = reordered['modules'].values.tolist()
    reordered_labels = reordered['labels'].values.tolist()

    newlabels_file = os.path.join(os.getcwd(), 'newlabels.tsv')
    out.to_csv(newlabels_file, sep='\t')
    return relabel_file, reordered_modules, reordered_labels, newlabels_file


def TsExtractor(labels, labelmap, func, mask, global_signal=True, pca=False, outfile="reg_timeseries.tsv",
                outlabelmap="individual_gm_labelmap.nii.gz"):
    # todo: check method
    import os
    import nibabel as nib
    import numpy as np
    import pandas as pd

    func_data = nib.load(func).get_data()
    labelmap_data = nib.load(labelmap).get_data()
    mask_data = nib.load(mask).get_data()

    labelmap_data[mask_data==0] = 0 # background

    outlab = nib.Nifti1Image(labelmap_data, nib.load(labelmap).affine)
    nib.save(outlab, outlabelmap)

    ret = []

    if global_signal:
        indices = np.argwhere(mask_data > 0)
        X = []
        for i in indices:
            x = func_data[i[0], i[1], i[2], :]
            if np.std(x) > 0.000001:
                X.append(x.tolist())
        if len(X) == 0:
            x = np.repeat(0, func_data.shape[3])
        elif pca:
            import sklearn.decomposition as decomp
            from sklearn.preprocessing import StandardScaler
            X = StandardScaler().fit_transform(np.transpose(X))
            PCA = decomp.PCA(n_components=1, svd_solver="arpack")
            x = PCA.fit_transform(X).flatten()
        else:
            x = np.mean(X, axis=0)
        ret.append(x)

    for l in range(1,len(labels)+1):
        indices=np.argwhere(labelmap_data == l)
        X = []
        for i in indices:
            x = func_data[i[0], i[1], i[2], :]
            if np.std(x) > 0.000001:
                X.append(x.tolist())
        X = np.array(X)
        if X.shape[0]==0:
            x=np.repeat(0,func_data.shape[3])
        elif X.shape[0]==1:
            x=X.flatten()
        elif pca:
            import sklearn.decomposition as decomp
            from sklearn.preprocessing import StandardScaler
            X = StandardScaler().fit_transform(np.transpose(X))
            PCA = decomp.PCA(n_components=1, svd_solver="arpack")
            x = PCA.fit_transform(X).flatten()
        else:
            x = np.mean(X, axis=0)
        ret.append(x)

    ret = np.transpose(np.array(ret))

    if global_signal:
        labels = ["GlobSig"] + labels

    ret = pd.DataFrame(data=ret, columns=labels)

    ret.to_csv(outfile, sep="\t", index=False)

    return os.path.join(os.getcwd(), outfile), labels, os.path.join(os.getcwd(), outlabelmap)



def plot_carpet_ts(timeseries, modules, atlas=None, background_file=None, subplot=None, output_file="regts.png"):
    """
    Adapted from: https://github.com/poldracklab/niworkflows

    Plot an image representation of voxel intensities across time also know
    as the "carpet plot" or "Power plot". See Jonathan Power Neuroimage
    2017 Jul 1; 154:150-158.

    Parameters:
        timeseries (numpy.ndarray): 4D input image. See http://nilearn.github.io/manipulating_images/input_output.html.
        output_file (str, None): Optional! The name of the output image. Valid extensions are .png, .pdf, .svg.
    """
    import numpy as np
    import nibabel as nb
    import pandas as pd
    import os
    import matplotlib.pyplot as plt
    from matplotlib import gridspec as mgs
    import matplotlib.cm as cm
    from matplotlib.colors import ListedColormap
    from nilearn.plotting import plot_img

    legend = False
    if atlas:
        legend = True

    # actually load data
    timeseries = pd.read_csv(timeseries, sep="\t")

    #normalise all timeseries
    v = (None, None)
    timeseries = (timeseries - timeseries.mean()) / timeseries.std()
    v = (-2, 2)
    timeseries = timeseries.transpose()

    minimum = timeseries.min()
    maximum = timeseries.max()
    myrange = maximum - minimum

    modules = pd.Series(modules).values
    lut = pd.factorize(modules)[0]+1

    # If subplot is not defined
    if subplot is None:
        subplot = mgs.GridSpec(1, 1)[0]

    # Define nested GridSpec
    wratios = [2, 120, 20]
    gs = mgs.GridSpecFromSubplotSpec(1, 2 + int(legend), subplot_spec=subplot,
                                     width_ratios=wratios[:2 + int(legend)],
                                     wspace=0.0)

    mycolors = ListedColormap(cm.get_cmap('Set1').colors[:7][::-1])

    # Segmentation colorbar

    ax0 = plt.subplot(gs[0])

    ax0.set_yticks([])
    ax0.set_xticks([])

    lutt=pd.DataFrame({'1': lut})
    ax0.imshow(lutt, interpolation='none', aspect='auto',
               cmap=mycolors, vmin=0, vmax=8)

    ax0.grid(False)
    ax0.spines["left"].set_visible(False)
    ax0.spines["bottom"].set_color('none')
    ax0.spines["bottom"].set_visible(False)


    # Carpet plot
    ax1 = plt.subplot(gs[1])
    ax1.imshow(timeseries, interpolation='nearest', aspect='auto', cmap='gray',
               vmin=v[0], vmax=v[1])

    ax1.grid(False)
    ax1.set_yticks([])
    ax1.set_yticklabels([])

    # Set 10 frame markers in X axis
    interval = max((int(timeseries.shape[-1] + 1) // 10, int(timeseries.shape[-1] + 1) // 5, 1))
    xticks = list(range(0, timeseries.shape[-1])[::interval])
    ax1.set_xticks(xticks)
    ax1.set_xlabel('time')

    # Remove and redefine spines
    for side in ["top", "right"]:
        # Toggle the spine objects
        ax0.spines[side].set_color('none')
        ax0.spines[side].set_visible(False)
        ax1.spines[side].set_color('none')
        ax1.spines[side].set_visible(False)

    ax1.yaxis.set_ticks_position('left')
    ax1.xaxis.set_ticks_position('bottom')
    ax1.spines["bottom"].set_visible(False)
    ax1.spines["left"].set_color('none')
    ax1.spines["left"].set_visible(False)

    if legend:
        gslegend = mgs.GridSpecFromSubplotSpec(
            5, 1, subplot_spec=gs[2], wspace=0.0, hspace=0.0)

        if not background_file:
            background_file = atlas #TODO: works only for 3mm atlas
        background = nb.load(background_file)
        atlas = nb.load(atlas)

        nslices = background.shape[-1]
        coords = [-40, 20, 0, 20, 40]  # works in MNI space
        lut2 = lut
        lut2 = np.array([0] + lut2.tolist())

        relabeled=lut2[np.array(atlas.get_data(), dtype=int)]
        atl = nb.Nifti1Image(relabeled, atlas.affine)
        for i, c in enumerate(coords):
            ax2 = plt.subplot(gslegend[i])
            plot_img(atl, bg_img=background, axes=ax2, display_mode='z',
                     annotate=False, cut_coords=[c], threshold=0.1, cmap=mycolors,
                     interpolation='nearest', vmin=1, vmax=7)

    if output_file is not None:
        figure = plt.gcf()
        figure.savefig(output_file, bbox_inches='tight')
        plt.close(figure)
        figure = None
        return os.getcwd() + '/' + output_file

    return [ax0, ax1], gs