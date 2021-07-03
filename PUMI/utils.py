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
    # ref should be either 'head', 'brain' or 'brain_mask'
    if ref in ['head', 'brain', 'brain_mask', ]:
        path = wf.cfg_parser.get('TEMPLATES', ref.lower(), fallback=None)
        if path is None:
            # fallback values:
            if ref == 'head':
                return os.path.join(os.environ['FSLDIR'], 'data/standard/MNI152_T1_2mm.nii.gz')
            elif ref == 'brain':
                return os.path.join(os.environ['FSLDIR'], 'data/standard/MNI152_T1_2mm_brain.nii.gz')
            else:
                return os.path.join(os.environ['FSLDIR'], 'data/standard/MNI152_T1_2mm_brain_mask_dil.nii.gz')

        if path.startswith('/'):
            return path
        else:
            return os.path.join(os.environ['FSLDIR'], path)
    else:
        raise ValueError("Can only provide references for 'head', 'brain', 'brain_mask'")


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
