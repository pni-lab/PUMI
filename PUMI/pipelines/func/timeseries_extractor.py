from PUMI.pipelines.func.func2standard import atlas2func
from nipype.interfaces import afni
import nipype.interfaces.utility as utility
from PUMI.engine import GroupPipeline, FuncPipeline, NestedNode as Node, QcPipeline
from PUMI.utils import relabel_atlas, get_reference, TsExtractor, plot_carpet_ts


@QcPipeline(inputspec_fields=['timeseries', 'modules', 'atlas'],
            outputspec_fields=[])
def extract_timeseries_nativespace_qc(wf, **kwargs):
    if wf.get_node('inputspec').inputs.atlas is None:
        wf.get_node('inputspec').inputs.atlas = None

    qc_timeseries = Node(interface=utility.Function(
        input_names=['timeseries', 'modules', 'output_file', 'atlas'],
        output_names=['plotfile'],
        function=plot_carpet_ts
    ),
        name="qc_timeseries"
    )
    qc_timeseries.inputs.output_file = "qc_timeseries.png"

    wf.connect('inputspec', 'timeseries', qc_timeseries, 'timeseries')
    wf.connect('inputspec', 'atlas', qc_timeseries, 'atlas')
    wf.connect('inputspec', 'modules', qc_timeseries, 'modules')
    wf.connect(qc_timeseries, 'plotfile', 'sinker', 'regTimeseriesQC')


@FuncPipeline(inputspec_fields=['atlas', 'labels', 'modules', 'anat', 'inv_linear_reg_mtrx', 'inv_nonlinear_reg_mtrx',
                                'func', 'gm_mask', 'confounds', 'confound_names'],
              outputspec_fields=['timeseries', 'out_gm_label'])
def extract_timeseries_nativespace(wf, global_signal=True, **kwargs):
    # this workflow transforms atlas back to native space and uses TsExtractor

    # 'anat', # only obligatory if stdreg==globals._RegType_.ANTS

    # transform atlas back to native EPI spaces!
    atlas2native = atlas2func('atlas2native', stdreg='ants')
    wf.connect('inputspec', 'atlas', atlas2native, 'inputspec.atlas')
    wf.connect('inputspec', 'anat', atlas2native, 'inputspec.anat')
    wf.connect('inputspec', 'inv_linear_reg_mtrx', atlas2native, 'inv_linear_reg_mtrx')
    wf.connect('inputspec', 'inv_nonlinear_reg_mtrx', atlas2native, 'inv_nonlinear_reg_mtrx')
    wf.connect('inputspec', 'func', atlas2native, 'func')
    wf.connect('inputspec', 'gm_mask', atlas2native, 'example_func')
    wf.connect('inputspec', 'confounds', atlas2native, 'confounds')
    wf.connect('inputspec', 'confound_names', atlas2native, 'confound_names')

    # extract timeseries
    extract_timeseries = Node(interface=utility.Function(input_names=['labels', 'labelmap', 'func', 'mask', 'global_signal'],
                                                         output_names=['out_file', 'labels', 'out_gm_label'],
                                                         function=TsExtractor),
                                     name='extract_timeseries')
    extract_timeseries.inputs.global_signal = global_signal
    wf.connect(atlas2native, 'atlas2func', extract_timeseries, 'labelmap')
    wf.connect('inputspec', 'labels', extract_timeseries, 'labels')
    wf.connect('inputspec', 'gm_mask', extract_timeseries, 'mask')
    wf.connect('inputspec', 'func', extract_timeseries, 'func')

    wf.connect(extract_timeseries, 'out_file', 'sinker', 'regional_timeseries')

    # QC
    timeseries_qc = extract_timeseries_nativespace_qc('extract_timeseries_nativespace_qc')
    wf.connect('inputspec', 'modules', timeseries_qc, 'modules')
    wf.connect('inputspec', 'atlas', timeseries_qc, 'atlas')
    wf.connect(extract_timeseries, 'out_file', timeseries_qc, 'timeseries')

    wf.connect(extract_timeseries, 'out_file', 'outputspec', 'timeseries')
    wf.connect(extract_timeseries, 'out_gm_label', 'outputspec', 'out_gm_label')


@GroupPipeline(inputspec_fields=['labelmap', 'modules', 'labels'],
              outputspec_fields=['relabeled_atlas', 'reordered_labels', 'reordered_modules'])
def pick_atlas(wf, reorder=True, **kwargs):

    resample_atlas = Node(
        interface=afni.Resample(
            outputtype='NIFTI_GZ',
            master=get_reference(wf, 'brain'),
        ),
        name='resample_atlas'
    )

    if reorder:
        # reorder if modules is given (like for MIST atlases)
        relabel_atls = Node(
            interface=utility.Function(
                input_names=['atlas_file', 'modules', 'labels'],
                output_names=['relabelled_atlas_file', 'reordered_modules', 'reordered_labels', 'newlabels_file'],
                function=relabel_atlas
            ),
            name='relabel_atls'
        )
        wf.connect('inputspec', 'labelmap', relabel_atls, 'atlas_file')
        wf.connect('inputspec', 'modules', relabel_atls, 'modules')
        wf.connect('inputspec', 'labels', relabel_atls, 'labels')

        wf.connect(relabel_atls, 'relabelled_atlas_file', resample_atlas, 'in_file')
    else:
        wf.connect('inputspec', 'labelmap', resample_atlas, 'in_file')

    # Sinking
    wf.connect(resample_atlas, 'out_file', 'sinker', 'atlas')
    if reorder:
        wf.connect(relabel_atls, 'newlabels_file', 'sinker', 'reordered_labels')
    else:
        wf.connect('inputspec', 'labels', 'sinker', 'atlas_labels')

    # Output
    wf.connect(resample_atlas, 'out_file', 'outputspec', 'relabeled_atlas')
    if reorder:
        wf.connect(relabel_atls, 'reordered_labels', 'outputspec', 'reordered_labels')
        wf.connect(relabel_atls, 'reordered_modules', 'outputspec', 'reordered_modules')
    else:
        wf.connect('inputspec', 'labels', 'outputspec', 'reordered_labels')
        wf.connect('inputspec', 'modules', 'outputspec', 'reordered_modules')