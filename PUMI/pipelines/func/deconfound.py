from nipype import Function
from nipype.interfaces import afni
from PUMI.engine import NestedNode as Node, QcPipeline
from PUMI.engine import FuncPipeline
from examples.carpet_plot import plot_carpet



@FuncPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file'])
def despiking_afni(wf, **kwargs):
    """
    todo
    """
    despike = Node(interface=afni.Despike(**kwargs), name='despike')
    despike.inputs.outputtype = 'NIFTI_GZ'
    wf.connect('inputspec', 'in_file', despike, 'in_file')
    wf.connect(despike, 'out_file', 'outputspec', 'out_file')

    # todo: qc
    qc_wf = qc('qc_wf')
    wf.connect(despike, 'out_file', qc_wf, 'in_file')


@QcPipeline(inputspec_fields=['in_file'],
            outputspec_fields=['out_file'])
def qc(wf):
    plot_interface = Function(
        input_names=['img', 'save_carpet'],
        output_names=['ax1'],
        function=plot_carpet,
        imports=['import os', 'import numpy as np', 'import nibabel as nb',
                 'import matplotlib.pyplot as plt', 'from matplotlib import gridspec as mgs',
                 'from nilearn._utils import check_niimg_4d',
                 'from nilearn._utils.niimg import _safe_get_data',
                 'from nilearn.signal import clean'])


    # Important because the default of save_plot is False
    plot_interface.inputs.save_carpet = True

    carpet_node = Node(name='carpet_node',
                       interface=plot_interface)

    wf.connect('inputspec', 'in_file', carpet_node, 'img')

    wf.connect(carpet_node, 'ax1', 'outputspec', 'out_file')


