import nipype.interfaces.utility as utility
from PUMI.engine import NestedNode as Node, GroupPipeline
from PUMI.utils import relabel_atlas, get_reference
from nipype.interfaces import afni


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