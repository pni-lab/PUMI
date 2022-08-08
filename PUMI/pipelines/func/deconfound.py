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


@FuncPipeline(inputspec_fields=['in_file', 'design_file'],
              outputspec_fields=['out_file'])
def nuisance_removal(wf, **kwargs):
    """

    Perform nuisance removal.

    CAUTION: Name in the old PUMI was nuissremov_workflow

    Parameters
    ----------


    Inputs
    ----------
    in_file (str): Path to reoriented motion corrected functional data.
    design_file (str): Path to matrix which contains all the nuissance regressors (motion + compcor noise + ...).

    Outputs
    ----------
    - Path to the filtered data

    Sinking
    ----------
    - Filtered data

    Acknowledgements
    ----------
    Adapted from Balint Kincses (2018)

    """
    from PUMI.pipelines.multimodal.image_manipulation import timecourse2png
    import nipype.interfaces.fsl as fsl

    nuisance_regression = Node(interface=fsl.FilterRegressor(filter_all=True), name='nuisance_regression')
    wf.connect('inputspec', 'in_file', nuisance_regression, 'in_file')
    wf.connect('inputspec', 'design_file', nuisance_regression, 'design_file')

    nuisance_removal_qc = timecourse2png('nuisance_removal_qc', sink=True)  # todo: check if correctly sinked
    wf.connect(nuisance_regression, 'out_file', nuisance_removal_qc, 'func')

    # sinking
    wf.connect(nuisance_regression, 'out_file', 'sinker', 'func_nuis_corrected')  # todo: check if correctly sinked

    # output
    wf.connect(nuisance_regression, 'out_file', 'outputspec', 'out_file')

