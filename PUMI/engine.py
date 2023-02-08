import argparse
from PUMI._version import get_versions
import os
from glob import glob
import warnings
from configparser import SafeConfigParser
from nipype.pipeline.engine.workflows import *
from nipype.pipeline.engine.nodes import *
import nipype.interfaces.utility as utility
from nipype.interfaces import BIDSDataGrabber
from nipype.interfaces.io import DataSink
from nipype import IdentityInterface, Function
from nipype.utils.filemanip import list_to_filename
from hashlib import sha1
import re
import ast

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

        @wraps(pipeline_fun) # So that decorated functions can be documented properly
        def wrapper(name, base_dir='.', sink_dir=None, qc_dir=None, **kwargs):

            cfg_parser = SafeConfigParser()
            cfg_parser.read(os.path.join(os.path.dirname(__file__), 'settings.ini'))

            if sink_dir is None:
                default_sink_dir = cfg_parser.get('SINKING', 'sink_dir', fallback='derivatives')
                if default_sink_dir.startswith('/'):
                    sink_dir = default_sink_dir
                else:
                    sink_dir = os.path.abspath(default_sink_dir)
            if qc_dir is None:
                default_qc_dir = cfg_parser.get('SINKING', 'qc_dir', fallback='derivatives/qc')
                if default_qc_dir.startswith('/'):
                    qc_dir = default_qc_dir
                else:
                    qc_dir = os.path.abspath(default_qc_dir)

            wf = NestedWorkflow(name, base_dir)
            wf.sink_dir = sink_dir
            wf.qc_dir = qc_dir
            wf.cfg_parser = cfg_parser

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

        if default_regexp_sub:
            substitutions = [(r'(.*\/)([^\/]+)\/([^\/]+)$', r'\g<1>\g<3>')]

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
                run_args = {'plugin':'MultiProc'}

            cfg_parser = SafeConfigParser()
            cfg_parser.read(os.path.join(os.path.dirname(__file__), 'settings.ini'))

            if sink_dir is None:
                default_sink_dir = cfg_parser.get('SINKING', 'sink_dir', fallback='derivatives')
                if default_sink_dir.startswith('/'):
                    sink_dir = default_sink_dir
                else:
                    sink_dir = os.path.abspath(os.path.join(base_dir, default_sink_dir))
            else:
                # Set default sink dir globally
                # todo: implement override in configparser?
                warnings.warn('Setting global sink_dir: Not yet implemented!\nModify settings.ini instead.')

            if qc_dir is None:
                default_qc_dir = cfg_parser.get('SINKING', 'qc_dir', fallback='derivatives/qc')
                if default_qc_dir.startswith('/'):
                    qc_dir = default_qc_dir
                else:
                    qc_dir = os.path.abspath(default_qc_dir)
            else:
                # Set default qc dir globally
                # todo: implement override in configparser?
                warnings.warn('Setting global qc_dir: Not yet implemented!\nModify settings.ini instead.')

            # main workflow
            wf = NestedWorkflow(name, base_dir)
            wf.sink_dir = sink_dir
            wf.qc_dir = qc_dir
            wf.cfg_parser = cfg_parser

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
                 working_dir=None, run_args=None, description=None, **kwargs):

        if description is None:
            self.parser = argparse.ArgumentParser()
        else:
            self.parser = argparse.ArgumentParser(description=description)

        self.parser.add_argument('--bids_dir', required=False, help='Root directory of the BIDS-compliant input dataset.')
        self.parser.add_argument('--output_dir', required=False, help='Directory where the results will be stored.')
        self.parser.add_argument('--analysis_level', required=False, choices=['participant'],
                                 help='Level of the analysis that will be performed. Default is participant.')
        self.parser.add_argument('--participant_label', required=False,
                                 help='Space delimited list of participant-label(s) (e.g. "001 002 003"). '
                                 'Perform the tool on the given participants or if this parameter is not '
                                 'provided then perform the procedure on all subjects.',
                                 nargs="+")
        self.parser.add_argument('--version', action='version', version='Version {}'.format(get_versions()['version']),
                                 help='Print version of PUMI')
        self.parser.add_argument('--working_dir', type=str,
                                 help='Directory where temporary data will be stored. Default is the current working directory.')

        self.parser.add_argument('--plugin', type=str,
                                 help='Nipype plugin (e.g. MultiProc, Slurm). If not set, MultiProc is used.')

        self.parser.add_argument('--n_procs', type=int,
                                 help='Amount of threads to execute in parallel.'
                                      + 'If not set, the amount of CPU cores is used.'
                                      + 'Caution: Does only work with the MultiProc-plugin!')

        self.parser.add_argument('--memory_gb', type=int,
                                 help='Memory limit in GB. If not set, use 90% of the available memory'
                                      + 'Caution: Does only work with the MultiProc-plugin!')

        self.parser.add_argument('--plugin_args', type=str,
                                 help='Nipype plugin arguments in dictionary format (e. g. {\'memory_gb\': 6})'
                                      + 'Caution: If set, you need to supply the --plugin argument and'
                                      + 'the command line arguments --n_procs and --memory_gb will be ignored!')

        self.pipeline = pipeline  # mandatory via script
        self.name = name  # mandatory via script
        self.bids_dir = bids_dir
        self.output_dir = output_dir
        self.analysis_level = analysis_level
        self.participant_label = participant_label
        self.working_dir = working_dir
        self.run_args = run_args
        self.kwargs = kwargs

    def run(self):
        cli_args = self.parser.parse_args()
        bids_specified = ['bids_dir', 'output_dir', 'analysis_level', 'participant_label', 'version', 'working_dir']
        pipeline_specific_arguments = {key:dict(vars(cli_args))[key] for key in dict(vars(cli_args)).keys() if key not in bids_specified}

        if cli_args.plugin_args is not None:
            plugin_args_dict = ast.literal_eval(cli_args.plugin_args)
            self.run_args = {'plugin': cli_args.plugin, 'plugin_args': plugin_args_dict}
        else:
            if cli_args.plugin is not None:
                self.run_args = {'plugin': cli_args.plugin}
            if cli_args.plugin == 'MultiProc':
                self.run_args['plugin_args'] = {}
                if cli_args.n_procs is not None:
                    self.run_args['plugin_args']['n_procs'] = cli_args.n_procs
                if cli_args.memory_gb is not None:
                    self.run_args['plugin_args']['memory_gb'] = cli_args.memory_gb

        if (cli_args.bids_dir is None) and (self.bids_dir is None):
            raise ValueError('The argument "bids_dir" has to be set!')
        else:
            self.bids_dir = cli_args.bids_dir if (cli_args.bids_dir is not None) else self.bids_dir

        if (cli_args.output_dir is None) and (self.output_dir is None):
            self.output_dir = './derivatives/'
        else:
            self.output_dir = cli_args.output_dir if (cli_args.output_dir is not None) else self.output_dir

        if (cli_args.analysis_level is None) and (self.analysis_level is None):
            self.output_dir = 'participant'
        else:
            self.output_dir = cli_args.analysis_level if (cli_args.analysis_level is not None) else self.analysis_level

        if (cli_args.participant_label is None) and (self.participant_label is None):
            self.output_dir = None
        else:
            self.output_dir = cli_args.participant_label if (cli_args.participant_label is not None) else self.participant_label

        if (cli_args.working_dir is None) and (self.working_dir is None):
            self.output_dir = '.'
        else:
            self.output_dir = cli_args.working_dir if (cli_args.working_dir is not None) else self.working_dir

        if self.run_args is None:
            self.pipeline(self.name, bids_dir=self.bids_dir, sink_dir=self.output_dir, base_dir=self.working_dir,
                          subjects=self.participant_label, **pipeline_specific_arguments, **self.kwargs)
        else:
            self.pipeline(self.name, bids_dir=self.bids_dir, sink_dir=self.output_dir, base_dir=self.working_dir,
                          subjects=self.participant_label, run_args=self.run_args, **pipeline_specific_arguments,
                          **self.kwargs)
