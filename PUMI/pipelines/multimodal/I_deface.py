from nipype import Function

from PUMI.engine import AnatPipeline
from PUMI.engine import NestedNode as Node

'''
Pipline for defacing anatomical images

infile : String
    Path to anat image

outfile : String
    Path to anat image
    If not specified, the output will be stored in the folder of the input.
    
    
force : Boolean
    set if existing deface image should be overwritten.

'''


@AnatPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file'])
def defacing(wf, **kwargs):
    from pydeface import utils
    deface_node = Node(Function(input_names=['infile', 'outfile', 'force'],
                                output_names=["outfile"],
                                function=utils.deface_image,
                                imports=[
                                    'import sys', 'import shutil', 'from nipype.interfaces import fsl',
                                    'from pydeface.utils import initial_checks, output_checks, generate_tmpfiles',
                                    'from pydeface.utils import cleanup_files, get_outfile_type, generate_tmpfiles',
                                    'from nibabel import load, Nifti1Image', 'import os']
                                ),
                       name='deface_node')

    deface_node.inputs.force = True

    wf.connect('inputspec', 'in_file', deface_node, 'infile')
    wf.connect('deface_node', 'outfile', 'outputspec', 'out_file')
