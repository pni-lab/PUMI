import argparse
from configparser import SafeConfigParser
from pathlib import Path
from PUMI._version import get_versions
from nipype.pipeline.engine.workflows import *
from nipype.pipeline.engine.nodes import *
import nipype.interfaces.utility as utility
from nipype.interfaces import BIDSDataGrabber
from nipype.interfaces.io import DataSink
from nipype import Function
from nipype.utils.filemanip import list_to_filename
from hashlib import sha1
import re
import ast
from PUMI import globals
import subprocess
import json


def _parameterization_dir(param):
    """
    Returns
        the directory name for the given parameterization string as follows:
        - If the parameterization is longer than 32 characters, then
          return the SHA-1 hex digest.
        - Otherwise, return the parameterization unchanged.
    """
    if len(param) > 32:
        return sha1(param.encode()).hexdigest()
    return param


class NestedNode(Node):
    # costumizing directories
    def output_dir(self):
        """Return the location of the output directory for the node"""
        # Output dir is cached
        if self._output_dir:
            return self._output_dir

        # Calculate & cache otherwise
        if self.base_dir is None:
            self.base_dir = mkdtemp()
        outputdir = self.base_dir

        # todo: maybe does not work with multiple mapnodes/iterables
        if self.parameterization:
            params_str = ["{}".format(p) for p in self.parameterization]
            # regexp magic to make subject handling more BIDS-like:
            #params_str = [re.sub('^_subject_', 'sub-', param) for param in params_str]
            if not str2bool(self.config["execution"]["parameterize_dirs"]):
                params_str = [_parameterization_dir(p) for p in params_str]

            if self._hierarchy:  # top level remains outside
                outputdir = op.join(outputdir, self._hierarchy.split(".")[0])
            outputdir = op.join(outputdir, *params_str)
            if self._hierarchy:  # subworkflows go inside
                outputdir = op.join(outputdir, *self._hierarchy.split(".")[1:])

        elif self._hierarchy:
            outputdir = op.join(outputdir, *self._hierarchy.split("."))

        self._output_dir = op.realpath(op.join(outputdir, self.name))

        if isinstance(self._interface, DataSink):
            if self.parameterization:
                params_str = ["{}".format(p) for p in self.parameterization]
                # regexp magic to make subject handling more BIDS-like:
                params_str = [re.sub('^_subject_', 'sub-', param) for param in params_str]
                if not str2bool(self.config["execution"]["parameterize_dirs"]):
                    params_str = [_parameterization_dir(p) for p in params_str]
                self._output_dir = op.join(self._output_dir, '-'.join(params_str))
                print(self._output_dir)

        return self._output_dir


class NestedMapNode(MapNode, NestedNode):
    # costumizing directories
    # output_dir() is from NestedNode
    def output_dir(self):
        return super().output_dir()


class NestedWorkflow(Workflow):
    # input/output filed naming is convenient: no need for 'inputspec.in_file' but simply 'in_file' (as if it was a node)
    # this is realized by tweaking the inputs of connect

    # plus: connect accepts names instead of objects (for using the pre-specified in/outpoutspec nodes)

    def connect(self, *args, **kwargs):

        """
        Todo docs
        """

        # we convert the input to handle the subworkflow-shortcuts
        # (i.e. adding 'inoutspec.' and 'outputspec.' when needed)

        if len(args) == 1:
            connection_list = args[0]
        elif len(args) == 4:
            connection_list = [(args[0], args[2], [(args[1], args[3])])]
        else:
            raise TypeError(
                "connect() takes either 4 arguments, or 1 list of"
                " connection tuples (%d args given)" % len(args)
            )

        connection_list = list(map(list, connection_list))

        # 1. Handle shortcut
        for i_conn_list, (srcnode, destnode, connects) in enumerate(connection_list):

            if isinstance(srcnode, str):
                connection_list[i_conn_list][0] = srcnode = self.get_node(srcnode)

            if isinstance(destnode, str):
                connection_list[i_conn_list][1] = destnode = self.get_node(destnode)

            for i_connects, (source, dest) in enumerate(connects):

                if isinstance(source, tuple):
                    # handles the case that source is specified
                    # with a function
                    sourcename = source[0]
                elif isinstance(source, (str, bytes)):
                    sourcename = source
                else:
                    raise Exception(
                        (
                            "Unknown source specification in "
                            "connection from output of %s"
                        )
                        % srcnode.name
                    )

                if sourcename and not srcnode._check_outputs(sourcename):
                    outputspec_source = 'outputspec.' + sourcename
                    if srcnode._check_outputs(outputspec_source):
                        connection_list[i_conn_list][2][i_connects] = (outputspec_source, dest)

                if not destnode._check_inputs(dest):
                    inputspec_dest = 'inputspec.' + dest
                    if destnode._check_inputs(inputspec_dest):
                        src = connection_list[i_conn_list][2][i_connects][0]
                        connection_list[i_conn_list][2][i_connects] = (src, inputspec_dest)
        # connect nodes
        super().connect(connection_list, **kwargs)


# decorator class
class PumiPipeline:

    """
     # Todo docs
    """

    def __init__(self, inputspec_fields=None, outputspec_fields=None, regexp_sub=None):
        if outputspec_fields is None:
            outputspec_fields = []
        if inputspec_fields is None:
            inputspec_fields = []
        if regexp_sub is None:
            regexp_sub = []
        self.inputspec_fields = inputspec_fields
        self.outputspec_fields = outputspec_fields
        self.regexp_sub = regexp_sub

    def __call__(self, pipeline_fun):

        from functools import wraps

        @wraps(pipeline_fun)  # So that decorated functions can be documented properly
        def wrapper(name, base_dir='.', sink_dir=None, qc_dir=None, **kwargs):

            if sink_dir is None:
                sink_dir = globals.cfg_parser.get('SINKING', 'sink_dir', fallback='derivatives')
                if not sink_dir.startswith('/'):
                    sink_dir = os.path.abspath(sink_dir)

            if qc_dir is None:
                qc_dir = globals.cfg_parser.get('SINKING', 'qc_dir', fallback='qc')
                if not qc_dir.startswith('/'):
                    qc_dir = os.path.abspath(os.path.join(sink_dir, qc_dir))

            wf = NestedWorkflow(name, base_dir)
            wf.sink_dir = sink_dir
            wf.qc_dir = qc_dir
            wf.cfg_parser = globals.cfg_parser

            if len(self.inputspec_fields) != 0:
                inputspec = NestedNode(
                    utility.IdentityInterface(
                        fields=self.inputspec_fields,
                        mandatory_inputs=True
                    ),
                    name='inputspec'
                )
                wf.add_nodes([inputspec])

            if len(self.outputspec_fields) != 0:
                outputspec = NestedNode(
                    utility.IdentityInterface(
                        fields=self.outputspec_fields,
                        mandatory_inputs=True
                    ),
                    name='outputspec'
                )
                wf.add_nodes([outputspec])

            sinker = NestedNode(
                DataSink(),
                name='sinker'
            )
            sinker.inputs.base_directory = wf.qc_dir if isinstance(self, QcPipeline) else wf.sink_dir
            sinker.inputs.regexp_substitutions = self.regexp_sub
            wf.add_nodes([sinker])

            pipeline_fun(wf=wf, **kwargs)

            # todo: should we do any post workflow checks
            # e.g. is outputspec connected
            # or unconnected nodes

            return wf

        return wrapper

    def _regex(self):
        print('Regexp substitutions:', self.regexp_sub)


class AnatPipeline(PumiPipeline):

    """
     # Todo docs
    """

    def __init__(self, inputspec_fields, outputspec_fields, regexp_sub=None, default_regexp_sub=True):
        regexp_sub = [] if regexp_sub is None else regexp_sub
        substitutions = []

        if default_regexp_sub:
            substitutions = [(r'(.*\/)([^\/]+)\/([^\/]+)\/([^\/]+)$', r'\g<1>\g<3>/\g<4>'),
                             ('_subject_', 'sub-')]
        substitutions.extend(regexp_sub)

        super().__init__(inputspec_fields, outputspec_fields, substitutions)

    def __call__(self, anat_fun):
        return super().__call__(anat_fun)


class QcPipeline(PumiPipeline):

    """
     # Todo docs
    """

    def __init__(self, inputspec_fields, outputspec_fields, regexp_sub=None, default_regexp_sub=True):
        regexp_sub = [] if regexp_sub is None else regexp_sub
        substitutions = []

        if default_regexp_sub:
            substitutions = [(r'(.*\/)([^\/]+)\/([^\/]+)$', r'\g<1>\g<2>.png'),
                             ('_subject_', 'sub-')]

        substitutions.extend(regexp_sub)
        super().__init__(inputspec_fields, outputspec_fields, substitutions)

    def __call__(self, qc_fun):
        return super().__call__(qc_fun)


class FuncPipeline(PumiPipeline):

    """
     # Todo docs
    """

    def __init__(self, inputspec_fields, outputspec_fields, regexp_sub=None, default_regexp_sub=True):
        regexp_sub = [] if regexp_sub is None else regexp_sub
        substitutions = []

        if default_regexp_sub:
            substitutions = [(r'(.*\/)([^\/]+)\/([^\/]+)\/([^\/]+)$', r'\g<1>\g<3>/\g<4>'),
                             ('_subject_', 'sub-')]

        substitutions.extend(regexp_sub)
        super().__init__(inputspec_fields, outputspec_fields, substitutions)

    def __call__(self, func_fun):
        return super().__call__(func_fun)


class GroupPipeline(PumiPipeline):

    def __init__(self, inputspec_fields, outputspec_fields, regexp_sub=None, default_regexp_sub=True):
        regexp_sub = [] if regexp_sub is None else regexp_sub
        substitutions = []

        cfg_parser = SafeConfigParser()
        cfg_parser.read('settings.ini')

        sink_dir = cfg_parser.get('SINKING', 'sink_dir', fallback='derivatives')
        if default_regexp_sub:
            substitutions = [(r'(.*\/)([^\/]+)\/([^\/]+)$', r'\g<1>//group/\g<2>/\g<3>')]

        substitutions.extend(regexp_sub)
        super().__init__(inputspec_fields, outputspec_fields, substitutions)

    def __call__(self, group_fun):
        return super().__call__(group_fun)


class BidsPipeline(PumiPipeline):

    """

    decorator for top-level pipelines, with BIDS input

    """


    def __init__(self, output_query=None):
        #regexp_sub = [] if regexp_sub is None else regexp_sub
        #substitutions = []
        #if default_regexp_sub:
        #    substitutions = []  # not needed here probably?
        #substitutions.extend(regexp_sub)

        if output_query is None:
            self.output_query = {
                'T1w': dict(
                    datatype='anat',
                    suffix='T1w',
                    extension=['nii', 'nii.gz']
                ),
                #'rest': dict(   # todo: how to get rests only
                #    datatype='func',
                #    suffix='bold',
                #    extension=['nii', 'nii.gz']
                #),
                'bold': dict(  # this should get all task, only
                    datatype='func',
                    suffix='bold',
                    extension=['nii', 'nii.gz']
                ),
                #'fmap': dict(
                #    modality='fmap',
                #    extension=['nii', 'nii.gz']
                #)
                #'dwi': dict(
                #    modality='dwi',
                #    extension=['nii', 'nii.gz']
                #)
            }
        else:
            self.output_query = output_query

        super().__init__(None, None, None)

    def __call__(self, pipeline_fun):
        def wrapper(name, bids_dir, subjects=None, base_dir='.', sink_dir=None, qc_dir=None, run_args=None, **kwargs):

            """
            # Todo Docs
            """

            # default: multiproc
            if run_args is None:
                run_args = {'plugin': 'MultiProc'}

            if sink_dir is None:
                sink_dir = globals.cfg_parser.get('SINKING', 'sink_dir', fallback='derivatives')
            if not sink_dir.startswith('/'):
                sink_dir = os.path.abspath(sink_dir)
            globals.cfg_parser.set('SINKING', 'sink_dir', sink_dir)

            if qc_dir is None:
                qc_dir = globals.cfg_parser.get('SINKING', 'qc_dir', fallback='qc')
            if not qc_dir.startswith('/'):
                qc_dir = os.path.abspath(os.path.join(sink_dir, qc_dir))
            globals.cfg_parser.set('SINKING', 'qc_dir', qc_dir)

            # main workflow
            wf = NestedWorkflow(name, base_dir)
            wf.sink_dir = sink_dir
            wf.qc_dir = qc_dir
            wf.cfg_parser = globals.cfg_parser

            # instead of inputspec, we need a bidsgrabber

            if subjects is None:
                # parse all subjects
                subjects = []
                for sub in glob(bids_dir + '/sub-*'):
                    subjects.append(sub.split('sub-')[-1])

            # Create a subroutine (subgraph) for every subject
            subject_iterator = Node(interface=utility.IdentityInterface(fields=['subject']), name='subject_iterator')
            subject_iterator.iterables = [('subject', subjects)]

            # create a BIDS-node
            bids_grabber = Node(BIDSDataGrabber(), name='bids_grabber')
            bids_grabber.inputs.base_dir = os.path.abspath(bids_dir)
            bids_grabber.inputs.output_query = self.output_query

            wf.connect(subject_iterator, 'subject', bids_grabber, 'subject')

            inputspec = NestedNode(
                utility.IdentityInterface(
                    fields=[*self.output_query]
                ),
                name='inputspec'
            )

            # 'Unpack' list from bids_grabber
            # bids_grabber returns a list with a string (path to the anat image of a subject),
            # but most other nodes do not take a list as input file
            for bids_modality in [*self.output_query]:
                print(bids_modality)
                path_extractor = Node(
                    Function(
                        input_names=["filelist"],
                        output_names=[bids_modality],
                        function=list_to_filename
                    ),
                    name="path_extractor_" + bids_modality
                )
                wf.connect(bids_grabber, bids_modality, path_extractor, 'filelist')
                wf.connect(path_extractor, bids_modality, inputspec, bids_modality)

            # there is no outputspec, this pipeline should not be nested!

            # in case it's needed:
            sinker = NestedNode(
                DataSink(),
                name='sinker'
            )
            sinker.inputs.base_directory = wf.qc_dir if isinstance(self, QcPipeline) else wf.sink_dir
            sinker.inputs.regexp_substitutions = self.regexp_sub
            wf.add_nodes([sinker])

            pipeline_fun(wf=wf, bids_dir=bids_dir, **kwargs)

            # todo: should we do any post workflow checks
            # e.g. is outputspec connected
            # or unconnected nodes

            wf.run(**run_args)
            return wf

        return wrapper


class BidsApp:

    def __init__(self, pipeline, name, bids_dir=None, output_dir=None, analysis_level=None, participant_label=None,
                 working_dir='.', run_args=None, description=None, **kwargs):

        if description is None:
            self.parser = argparse.ArgumentParser()
        else:
            self.parser = argparse.ArgumentParser(description=description)

        self.parser.add_argument(
            '--bids_dir',
            required=False,  # It's not required to supply agument via CLI, via BidsApp constructor is also fine!
            help='Root directory of the BIDS-compliant input dataset.'
        )

        self.parser.add_argument(
            '--output_dir',
            required=False,  # Not required to give via CLI, also possible to pass parameter via BidsApp constructor
            help='Directory where the results will be stored.'
        )

        self.parser.add_argument(
            '--analysis_level',
            required=False,
            choices=['participant'],
            help='Level of the analysis that will be performed. Default is participant.'

        )

        self.parser.add_argument(
            '--participant_label',
            required=False,
            help='Space delimited list of participant-label(s) (e.g. "001 002 003"). '
                 'Perform the tool on the given participants or if this parameter is not '
                 'provided then perform the procedure on all subjects.',
            nargs="+"
        )

        self.parser.add_argument(
            '--version',
            action='version',
            version='Version {}'.format(get_versions()['version']),
            help='Print version of PUMI'
        )

        self.parser.add_argument(
            '--working_dir',
            type=str,
            help='Directory where temporary data will be stored. Default is the current working directory.'
        )

        self.parser.add_argument(
            '--plugin',
            type=str,
            help='Nipype plugin (e.g. MultiProc, Slurm). If not set, MultiProc is used.'
        )

        self.parser.add_argument(
            '--n_procs',
            type=int,
            help='Amount of threads to execute in parallel. If not set, the amount of CPU cores is used.'
                 'Caution: Does only work with the MultiProc-plugin!')

        self.parser.add_argument(
            '--memory_gb',
            type=int,
            help='Memory limit in GB. If not set, use 90 percent of the available memory'
                 'Caution: Does only work with the MultiProc-plugin!')

        self.parser.add_argument(
            '--plugin_args',
            type=str,
            help='Nipype plugin arguments in dictionary format encapsulated in a string (e. g. "{\'memory_gb\': 6})"'
                 'Caution: If you set --plugin_args, you must also set --plugin1'
                 'If you specified --n_procs or --memory_gb outside of your --plugin_args specification, then it will '
                 'be ignored!'
        )

        self.pipeline = pipeline  # mandatory via script
        self.name = name  # mandatory via script
        self.bids_dir = bids_dir
        self.output_dir = output_dir
        self.analysis_level = analysis_level
        self.participant_label = participant_label
        self.working_dir = working_dir
        self.kwargs = kwargs

        if run_args is None:
            self.run_args = {}
        else:
            self.run_args = run_args

    def run(self):

        cli_args = self.parser.parse_args()
        cli_args_dict = vars(cli_args)

        # We need to extract the pipeline specific arguments like 'brr'.
        # We have a list of arguments that are BidsApp or nipype related.
        # If an argument is not in that list then it's such a pipeline specific argument.
        not_pipeline_specific = [
            'help',
            'bids_dir',
            'output_dir',
            'analysis_level',
            'participant_label',
            'version',
            'working_dir',
            'plugin',
            'plugin_args',
            'n_procs',
            'memory_gb'
        ]

        pipeline_specific_arguments = {}
        for key in cli_args_dict:
            if key in not_pipeline_specific:
                continue
            else:
                pipeline_specific_arguments[key] = cli_args_dict[key]

        # Now we extract the nipype runtime arguments.
        # We prioritize arguments given via CLI. If an argument is not provided via CLI, check if it's provided via
        # the BidsApp constructor. If this is also not the case, use default of nipype or own specify own default value.

        if cli_args.plugin_args is not None:
            # If plugin_args was specified via CLI then we don't have to search for any other nipype running arguments
            # We just have to check that --plugin was also specified.
            if cli_args.plugin is None:
                raise ValueError('Error: If you specify --plugin_args, then you must also specify --plugin')
            plugin_args_dict = ast.literal_eval(cli_args.plugin_args)
            self.run_args = {'plugin': cli_args.plugin, 'plugin_args': plugin_args_dict}
        else:
            if cli_args.plugin is not None:  # parameter specified via CLI
                self.run_args['plugin'] = cli_args.plugin
            elif 'plugin' not in self.run_args:  # parameter not specified via CLI or BidsApp constructor
                self.run_args['plugin'] = 'MultiProc'  # we have to use a default value

            if self.run_args['plugin'] == 'MultiProc':

                if 'plugin_args' not in self.run_args:  # plugin_args also not set via constructor (nor CLI as we know)
                    self.run_args['plugin_args'] = {}

                if cli_args.n_procs is not None:
                    self.run_args['plugin_args']['n_procs'] = cli_args.n_procs
                # No problem if it's not set via CLI or BidsApp constructor. Nipype will handle this!

                if cli_args.memory_gb is not None:
                    self.run_args['plugin_args']['memory_gb'] = cli_args.memory_gb
                # Also not a problem if not set! Nipype will deal with this!

        if (cli_args.bids_dir is None) and (self.bids_dir is None):
            raise ValueError('The argument "bids_dir" has to be set!')
        else:
            self.bids_dir = cli_args.bids_dir if (cli_args.bids_dir is not None) else self.bids_dir

        # Use specification from CLI if available. Otherwise, use the specification from the BidsApp-constructor.
        # If output_dir is None, BidsApp and PumiPipeline are going to read the location from settings.ini
        self.output_dir = cli_args.output_dir if (cli_args.output_dir is not None) else self.output_dir
        self.participant_label = cli_args.participant_label if (cli_args.participant_label is not None) else self.participant_label
        self.working_dir = cli_args.working_dir if (cli_args.working_dir is not None) else self.working_dir

        # todo: integrate analysis_level

        self.pipeline(
            self.name,
            bids_dir=self.bids_dir,
            sink_dir=self.output_dir,
            base_dir=self.working_dir,
            subjects=self.participant_label,
            run_args=self.run_args,
            **pipeline_specific_arguments,
            **self.kwargs
        )


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


class ParameterCollector:
    """
    A class to collect and store parameters used in the pipeline.
    
    This class collects parameters from two main sources:
    1. settings.ini file (via cfg_parser)
    2. Workflow nodes and their interfaces
    
    The collected parameters are stored in a structured format and are automatically
    converted to JSON-serializable values.
    """
    def __init__(self, wf):
        """
        Initialize the ParameterCollector.
        
        Args:
            wf: The workflow object containing the configuration parser and nodes.
        """
        self.wf = wf
        self.parameters = {
            'settings': {},  # Parameters from settings.ini
            'workflow': {}   # Parameters from workflow nodes
        }
        
    def _is_undefined(self, value):
        """
        Check if a value is an Undefined trait value.
        
        Args:
            value: The value to check
            
        Returns:
            bool: True if the value is undefined, False otherwise
        """
        return str(type(value)).endswith("._Undefined'>")
        
    def _convert_value(self, value):
        """
        Convert a value to a JSON-serializable format.
        
        Args:
            value: The value to convert
            
        Returns:
            The converted value that is JSON-serializable
        """
        if value is None or self._is_undefined(value):
            return None
        elif isinstance(value, Path):
            return str(value)
        elif hasattr(value, '__module__') and 'matplotlib' in str(value.__module__):
            return str(value)  # Convert matplotlib objects to strings
        elif hasattr(value, 'trait_type'):  # Handle CTrait objects
            try:
                if hasattr(value, 'value'):
                    actual_value = value.value
                elif hasattr(value, 'get'):
                    actual_value = value.get()
                else:
                    actual_value = value
                return self._convert_value(actual_value)  # Recursively convert the actual value
            except (AttributeError, TypeError):
                return str(value)
        elif hasattr(value, '__dict__'):
            # For objects with __dict__, try to get their string representation
            return str(value)
        return value
        
    def _is_empty(self, value):
        """
        Check if a value is empty or contains only empty values.
        
        Args:
            value: The value to check
            
        Returns:
            bool: True if the value is empty, False otherwise
        """
        if value is None:
            return True
        elif isinstance(value, (list, tuple, set)):
            return len(value) == 0
        elif isinstance(value, dict):
            return all(self._is_empty(v) for v in value.values())
        return False
        
    def collect_from_settings(self):
        """
        Collect parameters from settings.ini file.
        
        This method reads all sections and their key-value pairs from the config parser,
        converts the values to JSON-serializable format, and stores them in the settings
        dictionary. Empty sections are removed.
        """
        if not hasattr(self.wf, 'cfg_parser'):
            return
            
        try:
            for section in self.wf.cfg_parser.sections():
                self.parameters['settings'][section] = {}
                for key, value in self.wf.cfg_parser.items(section):
                    converted_value = self._convert_value(value)
                    if not self._is_empty(converted_value):
                        self.parameters['settings'][section][key] = converted_value
                        
                # Remove empty sections
                if not self.parameters['settings'][section]:
                    del self.parameters['settings'][section]
        except Exception as e:
            print(f"Warning: Error collecting settings parameters: {e}")
                
    def collect_from_workflow(self):
        """
        Collect parameters from workflow nodes.
        
        This method iterates through all nodes in the workflow, collects their input
        parameters, converts them to JSON-serializable format, and stores them in the
        workflow dictionary. Empty nodes are removed.
        """
        try:
            for node_name in self.wf.list_node_names():
                node = self.wf.get_node(node_name)
                if hasattr(node, 'interface') and hasattr(node.interface, 'inputs'):
                    self.parameters['workflow'][node_name] = {}
                    # Get the actual input values that were set
                    for trait_name, trait in node.interface.inputs.traits().items():
                        if trait_name in node.interface.inputs.__dict__:
                            value = node.interface.inputs.__dict__[trait_name]
                            converted_value = self._convert_value(value)
                            if not self._is_empty(converted_value):
                                self.parameters['workflow'][node_name][trait_name] = converted_value
                                
                    # Remove empty nodes
                    if not self.parameters['workflow'][node_name]:
                        del self.parameters['workflow'][node_name]
        except Exception as e:
            print(f"Warning: Error collecting workflow parameters: {e}")
                        
    def collect_all(self):
        """
        Collect all parameters from various sources.
        
        Returns:
            dict: A dictionary containing all collected parameters, organized by source
        """
        self.collect_from_settings()
        self.collect_from_workflow()
        return self.parameters

def create_dataset_description(wf,
                               pipeline_description_name,
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
    parameter_collector = ParameterCollector(wf)
    parameters = parameter_collector.collect_all()

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
            'Software': [{'Name': name, 'Version': version} for name, version in software_versions.items()],
            'Parameters': parameters
        }
    }

    with open(dataset_description_path, 'w') as outfile:
        json.dump(dataset_description, outfile, indent=4)
