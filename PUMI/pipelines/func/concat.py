from PUMI.engine import FuncPipeline, NestedNode as Node
from PUMI.utils import concatenate


@FuncPipeline(inputspec_fields=['par1', 'par2', 'par3', 'par4', 'par5', 'par6', 'par7', 'par8', 'par9', 'par10'],
              outputspec_fields=['concat_file'])
def concat(wf, fname='parfiles.txt', **kwargs):
    """
    Concatenate up to 10 nuissance regressors in one txt file. Inputs should be 'txt' files.
    """

    from nipype.interfaces.utility import Function

    conc = Node(
        interface=Function(
            input_names=['par1', 'par2', 'par3', 'par4', 'par5', 'par6', 'par7', 'par8', 'par9', 'par10'],
            output_names='out_file',
            function=concatenate
        ),
        name='concatenate'
    )

    for i in range(1, 10 + 1):
        actparam = "par" + str(i)
        wf.connect('inputspec', actparam, conc, actparam)

    wf.connect(conc, 'out_file', 'outputspec', 'concat_file')