from nipype.pipeline.engine.nodes import *
from nipype.interfaces.io import DataSink
from hashlib import sha1
import re


class NestedNode(Node):

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