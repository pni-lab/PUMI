from configparser import SafeConfigParser
from nipype.pipeline.engine.nodes import Node
import nipype.interfaces.utility as utility
from nipype.interfaces import BIDSDataGrabber
from nipype.interfaces.io import DataSink
from nipype import Function
from nipype.utils.filemanip import list_to_filename
from PUMI import globals
from PUMI.engine import NestedWorkflow, NestedNode
import os
from glob import glob


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

    @staticmethod
    def get_bids_inputs():
        """
        Get BIDS input configuration from settings.ini

        Returns:
            Dictionary containing the BIDS output query configuration
        """
        if not globals.cfg_parser.has_section('BIDS_INPUTS'):
            raise ValueError('BIDS_INPUTS section not found in settings.ini')

        input_names = globals.cfg_parser.options('BIDS_INPUTS')

        # Convert to output_query format
        output_query = {}
        for name in input_names:
            config_str = globals.cfg_parser.get('BIDS_INPUTS', name)
            if config_str.split(':') == 4:
                datatype, acquisition, suffix, extension = [item.strip() for item in config_str.split(':')]

                output_query[name] = {
                    'datatype': datatype,
                    'acquisition': acquisition,
                    'suffix': suffix,
                    'extension': extension.split(',') if ',' in extension else extension
                }
            elif config_str.split(':') == 3:
                datatype, suffix, extension = [item.strip() for item in config_str.split(':')]

                output_query[name] = {
                    'datatype': datatype,
                    'suffix': suffix,
                    'extension': extension.split(',') if ',' in extension else extension
                }
            else:
                raise ValueError(
                    'Format must be "name = datatype:suffix:possible_extension_1,possible_extension_2"'
                    + 'or: "name = datatype:acquisition:suffix:possible_extension_1,possible_extension_2"'
                )

        return output_query


    def __init__(self, output_query=None):

        if isinstance(output_query, dict):
            # If output_query is a dict, use it directly (old way)
            self.output_query = output_query
        elif output_query is None:
            # If output_query is None, get the inputs from settings.ini
            self.output_query = self.get_bids_inputs()
        else:
            raise ValueError('output_query must be a dict or None!')

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
