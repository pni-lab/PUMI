from nipype.interfaces import afni
from PUMI.engine import NestedNode as Node
from PUMI.engine import FuncPipeline


# Inputspec  is the input of the workflow
# Outputspec is the output of the workflow


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

    #todo: qc





