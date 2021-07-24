from templateflow import api as tflow
import subprocess
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


def registration_ants_hardcoded(brain, reference_brain, head, reference_head):
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
