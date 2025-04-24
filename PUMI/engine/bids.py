import argparse
from nipype.interfaces import BIDSDataGrabber
from nipype.interfaces.io import DataSink
from nipype import Function
from nipype.utils.filemanip import list_to_filename
from .pipelines import PumiPipeline
import subprocess
import json
import os
from pathlib import Path
from PUMI._version import get_versions
from PUMI import globals
from .base import NestedWorkflow
from glob import glob
import nipype.interfaces.utility as utility
from .base import NestedNode
from nipype.pipeline.engine.nodes import Node
from .pipelines import QcPipeline

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

