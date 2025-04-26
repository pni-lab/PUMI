import hashlib

from nipype.interfaces import BIDSDataGrabber

from PUMI._version import get_versions
from nipype.pipeline.engine.nodes import *
import subprocess
import json


def get_interface_version(interface):
    """

    Try to get the version number of the underlying tool used in an interface.

    Return None if interface is a nipype in-house interface that does not use external software like FSL.
    Otherwise, return name of the tool and the version number of the underlying used tool (or 'Unknown' if the
    version could not be fetched).

    """

    # Nipype provides some in-house interfaces that do not use external software like FSL.
    # We can exclude modules:
    NIPYPE_IN_HOUSE_MODULES = [
        'nipype.algorithms.',
        'nipype.interfaces.image.',
        'nipype.interfaces.io.',
        'nipype.interfaces.mixins.',
        'nipype.interfaces.utility.'
    ]

    interface_name = str(type(interface))  # e.g., "<class 'nipype.interfaces.fsl.utils.Reorient2Std'>"
    interface_name = interface_name.replace("<class \'", "")  # e.g., "nipype.interfaces.fsl.utils.Reorient2Std'>"
    interface_name = interface_name.replace("\'>", "")  # e.g., "nipype.interfaces.fsl.utils.Reorient2Std"
    # Let's see if it's a nipype in-house interface
    for in_house in NIPYPE_IN_HOUSE_MODULES:
        if in_house in interface_name:
            return None

    tool_name = interface_name.split('.')[2]  # e.g., 'fsl', 'ants', 'afni'

    try:
        version = interface.version
        if version is not None:
            return tool_name, version
    except AttributeError:
        pass

    if 'afni' in interface_name:
        version_cmd = ['afni', '-ver']
    elif 'ants' in interface_name:
        version_cmd = ['antsRegistration', '--version']
    elif 'c3' in interface_name:
        version_cmd = ['c3d', '-version']
    else:
        return interface_name, 'Unknown'

    try:
        result = subprocess.run(version_cmd, capture_output=True, text=True)
        return tool_name, result.stdout.strip()
    except Exception as e:
        print(f"Error getting version for {interface_name}: {e}")
        return tool_name, 'Unknown'


def calculate_dataset_hash(bids_dir, output_query):
    """
    Calculate SHA256 hash of a BIDS dataset.
    Uses BIDSDataGrabber to get the exact files that will be used in the pipeline.
    """
    hasher = hashlib.sha256()

    grabber = BIDSDataGrabber()
    grabber.inputs.base_dir = os.path.abspath(bids_dir)
    grabber.inputs.output_query = output_query

    # Get all subjects
    subjects = []
    for sub in glob(os.path.join(bids_dir, 'sub-*')):
        subjects.append(os.path.basename(sub).split('sub-')[-1])

    # For each subject, get their files and hash them
    for subject in sorted(subjects):
        grabber.inputs.subject = subject
        result = grabber.run()

        # Get all files from the result and sort them
        files_to_hash = []
        for key, file_list in result.outputs.get_traitsfree().items():
            if isinstance(file_list, list):
                files_to_hash.extend(file_list)

        # Sort and hash the files
        for file_path in sorted(files_to_hash):
            try:
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
            except Exception:
                # Skip files that can't be read
                continue

    return hasher.hexdigest()


def create_dataset_description(wf,
                               pipeline_description_name,
                               dataset_hash,
                               dataset_description_name='Derivatives created by PUMI',
                               bids_version='1.9.0'):
    """

    Create and save dataset description JSON for the derivatives created by PUMI that includes details about the
    software versions used in the pipeline.

    Parameters:
        wf (Workflow object): The workflow object.
        pipeline_description_name (str): Name of the used pipeline (e.g., 'RCPL-Pipeline').
        dataset_description_name (str, optional): Name for the dataset. Default is 'Derivatives created by PUMI'.
        bids_version (str, optional): The BIDS version used. Default is '1.9.0'.

    Returns:
        None. A JSON file is created in the workflow's specified sink directory.

    """

    software_versions = {}

    for node_name in wf.list_node_names():
        node = wf.get_node(node_name)
        result = get_interface_version(interface=node.interface)

        if result is None:
            continue  # We can skip the external-tool-independent nipype in-house interfaces
        else:
            interface_name, version = result
            software_versions[interface_name] = version

    dataset_description_path = Path(wf.sink_dir) / 'dataset_description.json'
    dataset_description_path.parent.mkdir(parents=True, exist_ok=True)

    dataset_description = {
        'Name': dataset_description_name,
        'BIDSVersion': bids_version,
        'PipelineDescription': {
            'Name': pipeline_description_name,
            'Version': get_versions()['version'],
            'DataGrabber Hash': dataset_hash,
            'Software': [{'Name': name, 'Version': version} for name, version in software_versions.items()],
            'Settings': [{section: dict(wf.cfg_parser.items(section)) for section in wf.cfg_parser.sections()}]
        }
    }

    with open(dataset_description_path, 'w') as outfile:
        json.dump(dataset_description, outfile, indent=4)
