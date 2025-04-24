from .base import NestedNode, NestedWorkflow
import nipype.interfaces.utility as utility
from nipype.interfaces.io import DataSink
from nipype import Function
from PUMI import globals
from configparser import SafeConfigParser

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