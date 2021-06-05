import os
from configparser import SafeConfigParser

from nipype.pipeline.engine.workflows import *
from nipype.pipeline.engine.nodes import *
import nipype.interfaces.utility as utility
from nipype.interfaces.io import DataSink
from hashlib import sha1
import re
from PUMI import default


def _parameterization_dir(param):
    """
    Returns the directory name for the given parameterization string as follows:
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
                        connection_list[i_conn_list][2][i_connects] = (source, inputspec_dest)

        # connect nodes
        super().connect(connection_list, **kwargs)


# decorator class
class PumiPipeline:

    def __init__(self, inputspec_fields, outputspec_fields, regexp_sub=None):
        if regexp_sub is None:
            regexp_sub = []
        self.inputspec_fields = inputspec_fields
        self.outputspec_fields = outputspec_fields
        self.regexp_sub = regexp_sub

    def __call__(self, pipeline_fun):
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

            inputspec = NestedNode(
                utility.IdentityInterface(
                    fields=self.inputspec_fields,
                    mandatory_inputs=True
                ),
                name='inputspec'
            )

            outputspec = NestedNode(
                utility.IdentityInterface(
                    fields=self.outputspec_fields,
                    mandatory_inputs=True
                ),
                name='outputspec'
            )

            sinker = NestedNode(
                DataSink(),
                name='sinker'
            )
            sinker.inputs.base_directory = wf.qc_dir if isinstance(self, QcPipeline) else wf.sink_dir
            sinker.inputs.regexp_substitutions = self.regexp_sub

            wf.add_nodes([inputspec, outputspec, sinker])
            pipeline_fun(wf=wf, **kwargs)

            # todo: should we do any post workflow checks
            # e.g. is outputspec connected
            # or unconnected nodes

            return wf

        return wrapper

    def _regex(self):
        print('Regexp substitutions:', self.regexp_sub)


class AnatPipeline(PumiPipeline):

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

    def __init__(self, inputspec_fields, outputspec_fields, regexp_sub=None, default_regexp_sub=True):
        regexp_sub = [] if regexp_sub is None else regexp_sub
        substitutions = []

        if default_regexp_sub:
            substitutions = [(r'(.*\/)([^\/]+)\/([^\/]+)\/([^\/]+)$', r'\g<1>\g<4>/\g<3>.png'),
                             ('_subject_', 'sub-')]

        substitutions.extend(regexp_sub)
        super().__init__(inputspec_fields, outputspec_fields, substitutions)

    def __call__(self, qc_fun):
        return super().__call__(qc_fun)


class FuncPipeline(PumiPipeline):

    def __init__(self, inputspec_fields, outputspec_fields, regexp_sub=None, default_regexp_sub=True):
        regexp_sub = [] if regexp_sub is None else regexp_sub
        substitutions = []

        if default_regexp_sub:
            substitutions = []  # coming soon

        substitutions.extend(regexp_sub)
        super().__init__(inputspec_fields, outputspec_fields, substitutions)

    def __call__(self, func_fun):
        return super().__call__(func_fun)
