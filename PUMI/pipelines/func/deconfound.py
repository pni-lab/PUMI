from nipype.interfaces import afni
from PUMI.engine import NestedNode as Node
from PUMI.engine import FuncPipeline



@FuncPipeline(inputspec_fields=['in_file'],
              outputspec_fields=['out_file'])
def despiking_afni(wf, **kwargs):
    despike = Node(interface=afni.Despike(), name='despike')
    despike.inputs.outputtype = 'NIFTI_GZ'
    wf.connect('inputspec', 'in_file', despike, 'in_file')
    wf.connect(despike, 'out_file', 'sinker', 'out_file')
    wf.connect(despike, 'out_file', 'outputspec', 'out_file')





