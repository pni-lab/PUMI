from templateflow import api as tflow
import os
from pathlib import Path

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

def get_reference(wf, ref_type=None, ref_path=None, allow_fsl_fallbacks=False):
    """
    Retrieves the reference path based on the provided type or path.

    Parameters:
        wf (object): The workflow object.
        ref_type (str, optional): The type of reference to fetch (e.g., 'head'). Defaults to None.
        ref_path (str, optional): Local or templateflow path to the reference. Defaults to None.
        allow_fsl_fallbacks (bool, optional): Whether to allow fallback references from FSL. Defaults to False.

    Returns:
        str: The resolved reference path.

    Raises:
        Exception: If both ref_type and ref_path are not provided.
        ValueError: If the source in ref_path is not 'local' or 'templateflow'/'tf'.

    Notes:
        - ref_path, if given, takes priority over ref_type
        - Example ref_path's:
            - 'data/standard/MNI152_T1_2mm.nii.gz; source=fsl'
            - 'tpl-MNI152Lin/tpl-MNI152Lin_res-02_T1w.nii.gz; source=templateflow'
            - 'MNI152Lin/tpl-MNI152Lin_res-02_T1w.nii.gz; source=tf'
    """
    if (not ref_type) and (not ref_path):
        raise Exception('It is not allowed to leave both ref_type and ref_path unset!')

    # If no ref_path is provided, try fetching from settings.ini
    if not ref_path:
        ref_path = wf.cfg_parser.get('TEMPLATES', ref_type, fallback='')
        if allow_fsl_fallbacks:
             ref_path = ref_path or get_fallback_reference(ref_type)

        if ref_path == '':
            raise Exception(f'allow_fsl_fallbacks is set to False, but ref path was not supplied nor was a suitable path defined for {ref_type} in settings.ini!')

    return parse_reference_path(ref_path)


def parse_reference_path(path):
    """
    Parse and resolve the reference path, handling various sources such as 'absolute', 'templateflow', and 'fsl'.

    Parameters:
        path (str): The reference path, possibly including a source identifier (e.g., 'source=templateflow').

    Returns:
        str: The resolved reference path.

    Raises:
        ValueError: If the source in the path is invalid or unsupported.
    """
    path = path.replace(' ', '')
    if ';source=' not in path:
        path += ';source=absolute'

    # Parse path and source, then handle accordingly
    path, source = path.split(';source=')
    if source == 'absolute':
        path = path
    elif source in {'templateflow', 'tf'}:
        path = get_ref_from_templateflow(path)
    elif source == 'fsl':
        path = os.path.join(os.environ['FSLDIR'], path)
    else:
        raise ValueError(
            f"Invalid source '{source}'. Allowed values are 'local' or 'templateflow' (or 'tf')."
        )

    return path


def get_fallback_reference(ref_type):
    """
    Returns the fallback reference path based on the given reference type.

    Parameters:
        ref_type (str): The type of reference for which the path is needed. Valid types are 'head', 'brain', 'brain_mask', 'ventricle_mask'.

    Returns:
        str: The file path of the fallback reference.

    Raises:
        Exception: If the provided ref_type is not valid.
    """
    fallback_references = {
        'head': os.path.join(os.environ['FSLDIR'], 'data/standard/MNI152_T1_2mm.nii.gz'),
        'brain': os.path.join(os.environ['FSLDIR'], 'data/standard/MNI152_T1_2mm_brain.nii.gz'),
        'brain_mask': os.path.join(os.environ['FSLDIR'], 'data/standard/MNI152_T1_2mm_brain_mask_dil.nii.gz'),
        'ventricle_mask': os.path.join(os.environ['FSLDIR'], 'data/standard/MNI152_T1_2mm_VentricleMask.nii.gz'),
    }

    ref_path = fallback_references.get(ref_type, '')

    if ref_path:
        return  ref_path
    else:
        raise Exception(f'{ref_type} is not one of the valid fallback reference: {fallback_references.keys()}')



def get_ref_from_templateflow(query):
    """
    Try to get the specified reference from templateflow and return the absolute path to the file.
    The schema for the query is either 'template/file' or 'file'.
    Look at the available references at 'https://www.templateflow.org/browse/'

    A possible query would be: 'tpl-MNI152Lin_res-02_T1w.nii.gz'
    Also okay:
    - 'tpl-MNI152Lin/tpl-MNI152Lin_res-02_T1w.nii.gz'
    - 'MNI152Lin/tpl-MNI152Lin_res-02_T1w.nii.gz'


    Parameters:
        query (str): The query string for the template reference, in the format 'template/file' or 'file'.

    Returns:
        str: The absolute path to the requested file.

    Raises:
        ValueError: If the query format is incorrect.
        Exception: If the specified file is not found in the templateflow archive.
    """

    if query.count('/') == 1:
        query = query.split('/')[1]

    components = {}
    for sub_string in query.split('_'):

        if '-' in sub_string:
            key, value = sub_string.split('-')

            if key == 'tpl':
                components['template'] = value
            elif key == 'res':
                components['resolution'] = value
            else:
                components[key] = value
        else:
            # Handle suffix and extension
            first_dot_idx = sub_string.index('.')
            components['suffix'] = sub_string[:first_dot_idx]
            components['extension'] = sub_string[first_dot_idx:]

    print(f'Generated templateflow search query for {query}: {components}')

    search_result = tflow.get(**components)
    if isinstance(search_result, list):
        for path in search_result:
            if Path(path).name == query:
                search_result = path
                break

    if isinstance(search_result, list):
        raise ValueError(f'{query} is not specific enough and yields multiple results: {search_result}')

    if search_result:
        return search_result
    else:
        raise Exception(
            f'Could not find the specified file. Are you sure {query} is available in the templateflow archive?'
        )