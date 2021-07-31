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

    Parameters
    ----------
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


def get_reference(wf, ref):
    """
    Returns the absolute path to the desired reference.
    Possible values for the ref parameter are 'head', 'brain' or 'brain_mask'.

    The method looks in the settings.ini for specified paths (and source specifications) for the desired reference in
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
    if ref not in ['head', 'brain', 'brain_mask']:
        raise ValueError('Can only provide references for \'head\', \'brain\', \'brain_mask\'')

    query = wf.cfg_parser.get('TEMPLATES', ref, fallback='')
    query = query.replace(' ', '')

    div = len(query.split(';source='))
    if div == 1:  # no occurrence of ';source=' (no source specification) -> search locally
        return get_ref_locally(wf, ref)
    elif div == 2:  # one occurrence of ';source=' (source was specified) -> look at the specification
        path, source = query.split(';source=')
        if source == 'local':
            return get_ref_locally(wf, ref)
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
    Possible values for the ref parameter are 'head', 'brain' or 'brain_mask'.

    The method looks in the settings.ini for specified paths for the desired reference in the TEMPLATES section.

    If no path was specified, the respective 2mm reference from FSL's standard repertoire is returned.
    If a path was specified, it is checked if the path starts with a '/'. If so, this path is considered as
    an absolute path, otherwise the path is considered relative to the FSL-Dir (NOT the current working directory)!
    """
    if ref not in ['head', 'brain', 'brain_mask']:
        raise ValueError('Can only provide references for \'head\', \'brain\', \'brain_mask\'')

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


def vol_id(in_file, ref_vol='last', raise_exception=False):
    # todo: really just for func??
    import nibabel
    image = nibabel.load(in_file)
    header = image.get_header()
    shape = header.get_data_shape()

    if len(shape) != 4 and raise_exception:
        raise TypeError('Input nifti file: %s is not a 4D file' % in_file)
    elif len(shape) != 4:
        print('''Input nifti file %s is not a 4D file, but raise_exception=False.
                 Return last slice of the func run''' % in_file)
        return 0

    numb_of_volumes = int(header.get_data_shape()[3])
    if ref_vol == 'first':
        vol_id = numb_of_volumes - 1
    elif ref_vol == 'middle':
        vol_id = int(round(numb_of_volumes/2))
    elif ref_vol == 'last':
        vol_id = 0  # todo: why is 0 the last slice??
    else:
        raise ValueError('''Can only provide the ID for the first, middle and last image.
                         %s is not a valid parameter for ref_vol''', ref_vol)
    return vol_id


def plot_roi(roi_img, bg_img=None, cut_coords=5, output_file=None, display_mode='mosaic', figure=None, axes=None,
             title=None, annotate=True, draw_cross=True, black_bg=True, threshold=0.5, alpha=0.7,
             cmap='tab10', dim='auto', vmin=None, vmax=None, resampling_interpolation='nearest', view_type='continuous',
             linewidths=2.5, colorbar=False, save_img=True, **kwargs):
    """

    Wrapper for nilearn's plot_roi method.

    Can be used in a nipype function node.
    Attention: In this case NO output_file should be specified (and save_img should stay True)!

    If no output_file is specified, the plot is stored as a png file in the current working directory.
    In case the function is executed within a nipype function node, the current working directory is the working
    directory of the respective node.

    Attention: This method returns unlike e.g. plot_brain_extraction_qc the plot object and the filename!

    Parameters
    ----------
    Only parameter that is not from nilearn's plot_roi method is save_img.
    Set to False if you don't want to save the result and just need the plot object.
    In this case the result is a tuple containing the plot object and None (otherwise it would be the plot
    object and the path to the file).

    For more information about the parameters, see the documentation of nilearn.
    https://nilearn.github.io/modules/generated/nilearn.plotting.plot_roi.html

    Only a few changes have been made to the default parameters.
    Here a mosaic plot with 5 columns is generated by default, the background of every plot is black and the default
    cmap has been changed.

    Returns
    ----------
    plot (nilearn.plotting.displays.OrthoSlicer): Plot object.
    output_file (str): Path to the saved plot.

    Acknowledgements
    ----------
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
    from PUMI.utils import plot_roi
    """

    Create segmentation (e.g. brain extraction, tissue segmentation) quality check images.

    Can be used in a nipype function node.
    Attention: In this case NO output_file should be specified (and save_imgshould stay True)!

    If no output_file is specified, the plot is stored as a png file in the current working directory.
    In case the function is executed within a nipype function node, the current working directory is the working
    directory of the respective node.

    Parameters
    ----------
    overlay (str): Path to the overlay (e.g. in brain extraction workflows the extracted brain).
    bg_img (str): Path to the background (e.g. in brain extraction workflows the head).
    output_file (str): Filename of quality check image. Can be be an absolute path or a relative path.
                       If it's set to None (default) and save_img is True, the filename is automatically generated.
    cmap (matplotlib colormap): Colormap.
    **kwargs: These parameters are passed to the plot_roi method.

    Returns
    ----------
    output_file (str): Path to the saved plot.

    """

    plot, output_file = plot_roi(roi_img=overlay, bg_img=bg_img, output_file=output_file, cut_coords=cut_coords,
                                 cmap=cmap, **kwargs)
    return output_file


def create_coregistration_qc(registered_brain, template, output_file=None, levels=None, cmap='winter', **kwargs):
    """

        Create coregistration quality check images.

        Can be used in a nipype function node.
        Attention: In this case NO output_file should be specified (and save_imgshould stay True)!

        If no output_file is specified, the plot is stored as a png file in the current working directory.
        In case the function is executed within a nipype function node, the current working directory is the working
        directory of the respective node.

        Parameters
        ----------
        registered_brain (str): Path to the registered brain.
        template (str): Path to the used template (reference) file.
        save_img (bool): Set to False if you don't want to save the result and just need the plot object.
                         In this case the result is a tuple containing the plot object and None (otherwise it would be
                         the plot object and the path to the file).
        output_file (str): Filename of quality check image. Can be be an absolute path or a relative path.
                           If it's set to None (default) and save_img is True, the filename is automatically generated.
        levels (list): Contour fillings levels. If set to None, [0.5] will be used.
        cmap (matplotlib colormap): Colormap.
        **kwargs: These parameters are passed to plot_roi method.

        Returns
        ----------
        plot (nilearn.plotting.displays.OrthoSlicer): Plot object.
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

