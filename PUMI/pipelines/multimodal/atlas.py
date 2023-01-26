from nipype.interfaces import afni
import nipype.interfaces.utility as utility
from PUMI.engine import GroupPipeline, NestedNode as Node, QcPipeline
from PUMI.utils import plot_roi

import os

@GroupPipeline(inputspec_fields=['atlas', 'atlas_params', 'labelmap_params', 'atlas_dir', 'modules_atlas', 'modules_params', 'modules_labelmap_params','modules_dir'],
              outputspec_fields=['labels','labelmap'])
def atlas_selection(wf,modularize=False,**kwargs):
    """
    Workflow to fetch an atlas and, optionally, perform a modularization step using another atlas.

    Decorator parameters:
        Input parameters:
            atlas: str
                Name of the atlas to be fetched. It can be a nilearn atlas ('aal','allen','basc',
                'craddock','destrieux','difumo','harvard_oxford','juelich','msdl','pauli','schaefer','surf_destrieux',
                'talairach','yeo') or a custom atlas
            atlas_params: dict
                Nilearn atlas parameters for 'atlas'.
            labelmap_params: tuple
                Nilearn atlas return data keys
            atlas_dir: str
                Path to custom atlas
            modules_atlas: str
                Equivalent to the 'atlas' parameter. This atlas will be used to modularize the first fetched atlas
            modules_params: dict
                Nilearn atlas parameters for 'modules_atlas'
            modules_labelmap_params: tuple
                Nilearn atlas return data keys for 'modules_atlas'
            modules_dir: str
                Path to custom 'modules_atlas'
        Output parameters:
            labels: Dataframe
                Labelmap labels with their associated region names
            labelmap: str
                Path to labelmap file

    Parameters:
        wf: str
            Name of the workflow
        modularize: bool, optional
            Whether to add the modularization step to the workflow. Default=False
        **kwargs:
            module_threshold: float, optional
                Number between 0 and 1 used in the modularize_atlas_module workflow. In the case that a region in 'atlas'
                and the background of 'modules_atlas' get the highest similarity score, this threshold will determine if
                the region is considered as not belonging to any modules or as part of the non-background module in
                'modules_atlas'
    """
    # Fetch atlas
    fetch_atlas_wf = fetch_atlas_module('fetch_atlas_wf')
    wf.connect('inputspec','atlas',fetch_atlas_wf,'name_atlas')
    wf.connect('inputspec', 'atlas_params', fetch_atlas_wf, 'atlas_params')
    wf.connect('inputspec', 'labelmap_params', fetch_atlas_wf, 'labelmap_params')
    wf.connect('inputspec', 'atlas_dir', fetch_atlas_wf, 'atlas_dir')

    # QC
    plot_labelmap = plot_atlas_qc('plot_atlas_qc')
    wf.connect(fetch_atlas_wf, 'labelmap', plot_labelmap, 'labelmap')

    if modularize:

        # Fetch modules atlas
        fetch_atlas_modules_wf = fetch_atlas_module('fetch_atlas_modules_wf')
        wf.connect('inputspec', 'modules_atlas', fetch_atlas_modules_wf, 'name_atlas')
        wf.connect('inputspec', 'modules_params', fetch_atlas_modules_wf, 'atlas_params')
        wf.connect('inputspec', 'modules_labelmap_params', fetch_atlas_modules_wf, 'labelmap_params')
        wf.connect('inputspec', 'modules_dir', fetch_atlas_modules_wf, 'atlas_dir')

        # QC
        plot_labelmap_modules = plot_atlas_qc('plot_atlas_modules_qc')
        wf.connect(fetch_atlas_modules_wf, 'labelmap', plot_labelmap_modules, 'labelmap')

        # Relabel labelmap, reorder labels, reorder modules
        modularize_wf = modularize_atlas_module('modularize_atlas_wf',**kwargs)
        wf.connect(fetch_atlas_wf,'labels',modularize_wf,'labels')
        wf.connect(fetch_atlas_wf, 'labelmap', modularize_wf, 'labelmap')
        wf.connect(fetch_atlas_modules_wf, 'labels', modularize_wf, 'labels_modules')
        wf.connect(fetch_atlas_modules_wf, 'labelmap', modularize_wf, 'labelmap_modules')

        # Sinking
        wf.connect(modularize_wf, 'relabelled_labelmap', 'sinker', 'relabelled_atlas')
        wf.connect(modularize_wf, 'reordered_labels', 'sinker', 'reordered_labels')

        # Output
        wf.connect(modularize_wf, 'relabelled_labelmap', 'outputspec', 'labelmap')
        wf.connect(modularize_wf, 'reordered_labels', 'outputspec', 'labels')

        # QC
        plot_relabelled_labelmap = plot_atlas_qc('plot_relabelled_atlas_qc')
        wf.connect(modularize_wf, 'relabelled_labelmap', plot_relabelled_labelmap, 'labelmap')

    else:

        # Sinking
        wf.connect(fetch_atlas_wf, 'labelmap', 'sinker', 'atlas')
        wf.connect(fetch_atlas_wf, 'labels', 'sinker', 'atlas_labels')

        # Output
        wf.connect(fetch_atlas_wf, 'labelmap', 'outputspec', 'labelmap')
        wf.connect(fetch_atlas_wf, 'labels', 'outputspec', 'labels')

    wf.write_graph('atlas_selection.png')

@GroupPipeline(inputspec_fields=['name_atlas', 'atlas_dir', 'atlas_params', 'labelmap_params'],
              outputspec_fields=['labels', 'labelmap'])
def fetch_atlas_module(wf, **kwargs):
    """
    Workflow to fetch an atlas.

    Decorator parameters:
        Input parameters:
            atlas: str
                Name of the atlas to be fetched. It can be a nilearn atlas ('aal','allen','basc','craddock','destrieux',
                'difumo','harvard_oxford','juelich','msdl','pauli','schaefer','surf_destrieux','talairach','yeo') or a
                custom atlas
            atlas_params: dict
                Nilearn atlas parameters for 'atlas'.
            labelmap_params: tuple
                Nilearn atlas return data keys
            atlas_dir: str
                Path to custom atlas
        Output parameters:
            labels: Dataframe
                Labelmap labels with their associated region names
            labelmap: str
                Path to labelmap file

    Parameters:
        wf: str
            Name of the workflow
        **kwargs:
    """
    fetch_atlas = Node(
        interface=utility.Function(
            input_names=['name_atlas', 'atlas_dir', 'atlas_params', 'labelmap_params'],
            output_names=['labels','labelmap'],
            function=get_atlas
        ),
        name='fetch_atlas'
    )

    wf.connect('inputspec', 'name_atlas', fetch_atlas, 'name_atlas')
    wf.connect('inputspec', 'atlas_params', fetch_atlas, 'atlas_params')
    wf.connect('inputspec', 'labelmap_params', fetch_atlas, 'labelmap_params')
    wf.connect('inputspec', 'atlas_dir', fetch_atlas, 'atlas_dir')

    # Sinking
    wf.connect(fetch_atlas, 'labelmap', 'sinker', 'atlas')
    wf.connect(fetch_atlas, 'labels', 'sinker', 'atlas_labels')

    # Output
    wf.connect(fetch_atlas, 'labelmap', 'outputspec', 'labelmap')
    wf.connect(fetch_atlas, 'labels', 'outputspec', 'labels')

    wf.write_graph('fetch_atlas_wf.png')

@QcPipeline(inputspec_fields=['labelmap'],
            outputspec_fields=[])
def plot_atlas_qc(wf, **kwargs):
    """
    Workflow to plot and save an atlas labelmap.

    Decorator parameters:
        Input parameters:
            labelmap: str
                Path to labelmap file

    Parameters:
        wf: str
            Name of the workflow
        **kwargs:
    """
    plot_atlas = Node(interface=utility.Function(
        input_names=['roi_img'],
        output_names=['plot_file'],
        function=plot_roi
    ),
        name="plot_atlas"
    )

    wf.connect('inputspec', 'labelmap', plot_atlas, 'roi_img')
    wf.connect(plot_atlas, 'plot_file', 'sinker', 'labelmap_plot_QC')

@GroupPipeline(inputspec_fields=['labels', 'labelmap', 'labels_modules', 'labelmap_modules'],
              outputspec_fields=['reordered_labels', 'relabelled_labelmap'])
def modularize_atlas_module(wf, **kwargs):
    """
    Workflow to modularize an atlas, i.e. reorder the labels, so that they reflect the modules of another atlas.

    Decorator parameters:
        Input parameters:
            labels: Dataframe
                Labelmap labels with their associated region names
            labelmap: str
                Path to labelmap file
            labels_modules: Dataframe
                Labelmap labels with their associated region names
            labelmap_modules: str
                Path to labelmap file
        Output parameters:
            reordered_labels: Dataframe
                Relabelled labelmap labels with their associated region and module names
            relabelled_labelmap: str
                Path to relabelled labelmap file

    Parameters:
        wf: str
            Name of the workflow
        **kwargs:
    """
    resample_atlas_modules = Node(
        interface=afni.Resample(
            outputtype='NIFTI_GZ',
        ),
        name='resample_atlas_modules'
    )

    modularize_atlas = Node(
        interface=utility.Function(
            input_names=['labels', 'labelmap', 'labels_modules', 'labelmap_modules_resampled','module_threshold'],
            output_names=['reordered_labels', 'relabelled_labelmap'],
            function=relabel_atlas
        ),
        name='modularize_atlas'
    )

    wf.connect('inputspec', 'labelmap_modules', resample_atlas_modules, 'in_file')
    wf.connect('inputspec', 'labelmap', resample_atlas_modules, 'master')

    wf.connect('inputspec', 'labels', modularize_atlas, 'labels')
    wf.connect('inputspec', 'labelmap', modularize_atlas, 'labelmap')
    wf.connect('inputspec', 'labels_modules', modularize_atlas, 'labels_modules')
    wf.connect(resample_atlas_modules, 'out_file', modularize_atlas, 'labelmap_modules_resampled')
    if 'module_threshold' in kwargs:
        modularize_atlas.inputs.mod_threshold = kwargs['module_threshold']

    # Sinking
    wf.connect(modularize_atlas, 'relabelled_labelmap', 'sinker', 'relabelled_atlas')
    wf.connect(modularize_atlas, 'reordered_labels', 'sinker', 'reordered_atlas_labels')

    # Output
    wf.connect(modularize_atlas, 'reordered_labels', 'outputspec', 'reordered_labels')
    wf.connect(modularize_atlas, 'relabelled_labelmap', 'outputspec', 'relabelled_labelmap')

    wf.write_graph('modularize_atlas_wf.png')

def get_atlas(name_atlas, atlas_dir=None, **kwargs):
    """
    Determines which atlas to fetch and returns labelmap and labels.

    Parameters:
        name_atlas: str
            Input string can be for: 'aal','allen','basc','craddock','destrieux','difumo','harvard_oxford','juelich',
            'msdl','pauli','schaefer','surf_destrieux','talairach','yeo'
        atlas_dir: str, optional
            Path to a custom atlas labelmap and label text file.
        **kwargs: dict
            Nilearn atlas parameters and return data dictionary keys.
            atlas_params: dict
                Nilearn atlas parameters
            labelmap_params: tuple
                Return data dictionary keys, optional threshold to obtain a deterministic atlas from a probabilistic
                atlas, and other specific paramters.
                    - Nilearn return data dictionary keys: str
                      For 'basc', the scale of the labelmap is expected to be provided as a number in string format.
                    - Threshold to obtain a deterministic atlas. Considerations:
                      For 'allen' and 'smith', this threshold needs to be provided as the second element in the tuple
                      after the nilearn return data dictionary key.
                      For 'difumo', 'masdl', and 'pauli', it is expected to be the first element in the tuple.
                    - Other parameters:
                      For 'craddock', no threshold is needed to obtain a  probabilistic atlas. The nilearn return data
                      dictionary key is expected as the first element of the tuple, and the second element is the volume
                      number (#) corresponding to the desired clustering level (K). More information about this can be
                      found at https://ccraddock.github.io/cluster_roi/atlases.html (Nilearn does not offer volume
                      number 44)

    Returns:
        labels: Dataframe
            Labelmap labels with their associated region names
        labelmap: str
            Path to labelmap file

    Raises:
        ValueError
        Raised when the atlas is not formatted correctly or if there is no
        match found.
    """

    import numpy as np
    import pandas as pd
    import nibabel as nb
    from nilearn import image
    from nilearn.datasets import atlas as nl_atlas
    from fnmatch import fnmatch
    import os
    from PUMI.pipelines.multimodal.atlas import dummy_labels, get_det_atlas

    # Separate atlas_params and labelmap_params from kwargs
    if kwargs:
        map_args = kwargs['labelmap_params']
        kwargs = kwargs['atlas_params']

    # Check if the requested atlas is a custom or nilearn atlas
    if atlas_dir:

        # Access custom atlas file
        if os.path.exists(atlas_dir):
            # Get labelmap and labels
            labelmap = atlas_dir + '/Parcellations/' + name_atlas + '.nii.gz'
            labels_file = atlas_dir + '/Parcel_information/' + name_atlas + '.csv'
            labels = pd.read_csv(labels_file, sep=";")
            labels = labels.values.tolist()
        else:
            raise ValueError('No atlas detected. Check query or atlas directory')

    else:

        # Obtain the name of the nilearn atlas function
        function_name = [x for x in dir(nl_atlas) if fnmatch(x, "fetch_atlas_" + name_atlas + "*")]

        if function_name:
            # Load atlas
            function_name = str(function_name[0])
            atlas_function = getattr(nl_atlas, function_name)
            atlas = atlas_function(**kwargs)

            # Get labelmap and labels of the selected atlas
            if name_atlas == 'aal':

                labelmap = atlas['maps']
                labels = pd.DataFrame({'Region': atlas['labels']}, index=list(map(int, atlas['indices'])))
                labels.loc[0] = ['Background']
                labels = labels.sort_index()
                labels.index.names = ['Label']

            elif name_atlas == 'allen':

                if len(map_args) == 1:
                    map_args = map_args[0]
                    thr = ()
                    spec = '_unthresholded_'
                elif len(map_args) == 2:
                    thr = map_args[1]
                    map_args = map_args[0]
                    spec = '_thr' + str(thr) + '_'
                else:
                    map_args = 'maps'
                    thr = ()
                    spec = '_unthresholded_'

                labelmap = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),
                                        'derivatives/allen' + spec + 'det.nii.gz')
                det_labelmap = get_det_atlas(atlas[map_args],*thr)
                nb.save(det_labelmap, labelmap)

                # Get indices that map the network labels to the labelmap indices
                df = pd.DataFrame.from_records(atlas['rsn_indices'], columns=['Networks', 'Region_id'])
                prov_labels = pd.DataFrame({'Region': np.concatenate(atlas['networks'])}, index=np.concatenate(df['Region_id']))
                labels = prov_labels.sort_index()
                labels.index = pd.RangeIndex(start=0, stop=len(labels))
                for x in range(len(labels)):
                    labels['Region'][x] = labels['Region'][x] + '_IC' + str(prov_labels.index.sort_values()[x])
                labels.loc[-1] = ['Background']
                labels.index += 1
                labels = labels.sort_index()

                # Provide extended label list with dummy labels for the 75 network option
                if 'maps' in map_args:
                    dlabels = dummy_labels(det_labelmap.get_fdata())
                    network_ids = list(prov_labels.index.sort_values())
                    for x in range(len(dlabels)):
                        if x in network_ids:
                            dlabels['Region'][x] = labels['Region'][network_ids.index(x) + 1]

                    labels = dlabels

                labels.index.names = ['Label']

            elif name_atlas == 'basc':

                # Get specified resolution for the labelmap
                scale = [x for x in dir(atlas) if map_args[0] in x][0]
                labelmap_file = nb.load(atlas[scale])
                labelmap = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),
                                        'derivatives/basc_' + scale + '_det.nii.gz')
                nb.save(labelmap_file, labelmap)
                # Get labels from provided MIST files
                labels_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))) + '/data_in/atlas/MIST/Parcel_Information/MIST_' + map_args[0] + '.csv'
                labels = pd.read_csv(labels_dir, delimiter=";")
                labels = pd.DataFrame({'Region': labels['label']})
                labels.loc[-1] = ['Background']
                labels.index += 1
                labels = labels.sort_index()
                labels.index.names = ['Label']

            elif name_atlas == 'craddock':

                # load selected labelmap
                nii = nb.load(atlas[map_args[0]])

                # choose volume with the specified clustering level
                volume = image.index_img(nii, map_args[1])
                labelmap = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),
                                        'derivatives/craddock_' + map_args[0] + '_K' + str(map_args[1]) + '_det.nii.gz')
                nb.save(volume, labelmap)

                # create dummy labels
                labels = dummy_labels(volume.get_fdata())
                labels.index.names = ['Label']

            elif name_atlas == 'destrieux':

                labelmap = atlas['maps']
                label_names = pd.DataFrame.from_records(atlas['labels'])
                label_names = label_names.iloc[:, 1]
                labels = pd.DataFrame({'Region': label_names})
                labels.index.names = ['Label']

            elif name_atlas == 'difumo':

                if map_args:
                    thr = map_args[0]
                    spec = '_thr' + str(thr) + '_'
                else:
                    thr = ()
                    spec = '_unthresholded_'

                labelmap = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),
                                        'derivatives/difumo' + spec + 'det.nii.gz')
                det_labelmap = get_det_atlas(atlas['maps'],*thr)
                nb.save(det_labelmap, labelmap)
                labels_file = atlas['labels']
                if ~isinstance(labels_file, pd.DataFrame):
                    labels_file = pd.DataFrame.from_records(labels_file)
                labels = labels_file.filter(['difumo_names','yeo_networks7','yeo_networks17'], axis=1)
                labels.loc[-1] = ['Background','No network found','No network found']
                labels.index += 1
                labels = labels.sort_index()
                labels = labels.rename({'difumo_names': 'Region'}, axis='columns')
                labels.index.names = ['Label']

            elif name_atlas == 'harvard_oxford':

                labelmap = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),
                                        'derivatives/harvard_oxford_' + kwargs['atlas_name'] + '_det.nii.gz')
                nb.save(atlas['maps'], labelmap)
                labels = pd.DataFrame({'Region': atlas['labels']})
                labels.index.names = ['Label']

            elif name_atlas == 'juelich':

                labelmap = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),
                                        'derivatives/juelich_' + kwargs['atlas_name'] + '_det.nii.gz')
                nb.save(atlas['maps'], labelmap)
                labels = pd.DataFrame({'Region': atlas['labels']})
                labels.index.names = ['Label']

            elif name_atlas == 'msdl':

                if map_args:
                    thr = map_args[0]
                    spec = '_thr' + str(thr) + '_'
                else:
                    thr = ()
                    spec = '_unthresholded_'

                labelmap = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),
                                        'derivatives/msdl' + spec + 'det.nii.gz')
                det_labelmap = get_det_atlas(atlas['maps'],*thr)
                nb.save(det_labelmap, labelmap)
                labels = pd.DataFrame({'Region': atlas['labels']})
                labels.index += 1
                if 0 in np.unique(det_labelmap.get_fdata()):
                    labels.loc[0] = ['Background']
                    labels = labels.sort_index()

                labels.index.names = ['Label']

            elif name_atlas == 'pauli':

                if kwargs:

                    if map_args:
                        thr = map_args[0]
                        spec = '_thr' + str(thr) + '_'
                    else:
                        thr = ()
                        spec = '_unthresholded_'

                    labelmap = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),
                                            'derivatives/pauli' + spec + 'det.nii.gz')
                    det_labelmap = get_det_atlas(atlas['maps'],*thr)
                    nb.save(det_labelmap, labelmap)

                else:
                    labelmap = atlas['maps']

                # Add 'Background' label
                labels = np.insert(atlas['labels'], 0, 'Background')
                labels = pd.DataFrame({'Region': labels})
                labels.index.names = ['Label']

            elif name_atlas == 'schaefer':

                labelmap = atlas['maps']
                # Add 'Background' label
                labels = np.insert(atlas['labels'], 0, 'Background')
                labels = pd.DataFrame({'Region': labels})
                labels.index.names = ['Label']

            elif name_atlas == 'smith':

                if len(map_args) == 1:
                    map_args = map_args[0]
                    thr = ()
                    spec = '_unthresholded_'
                elif len(map_args) == 2:
                    thr = map_args[1]
                    map_args = map_args[0]
                    spec = '_thr' + str(thr) + '_'

                labelmap = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),
                                        'derivatives/difumo' + spec + 'det.nii.gz')
                det_labelmap = get_det_atlas(atlas[map_args],*thr)
                nb.save(det_labelmap, labelmap)

                if '10' in map_args:
                    labels = ['Visual_medial', 'Visual_occipital', 'Visual_lateral', 'DMN', 'Cerebellum',
                              'Sensorimotor', 'Auditory', 'Executive_Control', 'FP_left', 'FP_right']
                    labels = pd.DataFrame({'Labels': labels})
                    labels.loc[-1] = ['Background']
                    labels.index += 1
                    labels = labels.sort_index()
                else:
                    labels = dummy_labels(det_labelmap.get_fdata())

                labels.index.names = ['Label']

            elif name_atlas == 'surf_destrieux':

                # Get labelmap of the specified hemisphere
                labelmap = atlas['map_' + map_args[0]]
                labels = pd.DataFrame({'Region': atlas['labels']})
                labels.index.names = ['Label']

            elif name_atlas == 'talairach':

                labelmap = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))), 'derivatives/talairach_' + kwargs['level_name'] + '.nii.gz')
                nb.save(atlas['maps'], labelmap)
                labels = pd.DataFrame({'Region': atlas['labels']})
                labels.index.names = ['Label']

            elif name_atlas == 'yeo':

                # Get labelmap and labels with the specified resolution
                nii = nb.load(atlas[map_args[0]])
                nii_data = nii.get_fdata()
                labelmap_orig = nii_data[:, :, :, 0]
                det_labelmap = nb.Nifti1Image(labelmap_orig, nii.affine, nii.header)
                labelmap = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),
                                        'derivatives/atlas_yeo_' + map_args[0] + '_det.nii.gz')
                nb.save(det_labelmap, labelmap)

                if '17' in map_args[0]:
                    # Labels for the 17 Yeo networks
                    labels = ['Background','Visual Central (Visual A)', 'Visual Peripheral (Visual B)', 'Somatomotor A',
                              'Somatomotor B', 'Dorsal Attention A', 'Dorsal Attention B',
                              'Salience / Ventral Attention A', 'Salience / Ventral Attention B',
                              'Limbic A', 'Limbic B', 'Control C', 'Control A', 'Control B', 'Temporal Parietal',
                              'Default C', 'Default A', 'Default B']
                else:
                    # Labels for the 7 Yeo networks
                    labels = ['Background','Visual', 'Somatomotor', 'Dorsal Attention', 'Salience / Ventral Attention',
                              'Limbic', 'Control', 'Default']

                labels = pd.DataFrame({'Region': labels})
                labels.index.names = ['Label']

        else:
            raise ValueError('No atlas detected. Check query string')

    # saving as tsv file
    labels_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),'atlas_files/' + name_atlas + '_labels.tsv')
    labels.to_csv(labels_path, sep="\t")

    return labels, labelmap

def dummy_labels(atlas_data):
    """
    When an atlas does not provide a labels file, this function creates dummy labels based on the provided labelmap.
    Parameters:
        atlas_data: numpy.ndarray
            Labelmap matrix
    Returns:
        labels: Dataframe
            Labels with dummy region names
    """
    import pandas as pd

    indices = list(map(round, list(set(atlas_data.flatten()))))
    print(indices)

    value_to_label_dict = [''] * len(indices)
    for pos, val in enumerate(indices):
        value_to_label_dict[pos] = 'Component ' + str(indices[pos])

    value_to_label_dict[0] = 'Background'

    labels = pd.DataFrame({'Region': value_to_label_dict})
    labels.index = indices

    return labels

def get_det_atlas(labelmap_4d, threshold=0):
    """
    Creates a 3D deterministic labelmap from a probabilistic atlas.
    Parameters:
        labelmap_4d: str
            Path to probabilistic labelmap (4D)
        threshold: float
            Voxels whose value is lower than the threshold will be considered to be 0

    Returns:
        deterministic_nii: nii.gz
            Deterministic atlas (3D)
    """
    import numpy as np
    import nibabel as nb
    import operator

    nii = nb.load(labelmap_4d)
    img_4d_data = nii.get_fdata()
    det_labelmap = np.zeros(img_4d_data.shape[:3])

    for x in np.ndindex(img_4d_data.shape[:3]):
        idx, value = max(enumerate(img_4d_data[x].flatten()), key=operator.itemgetter(1))
        if value > threshold:
            det_labelmap[x] = idx + 1

    deterministic_nii = nb.Nifti1Image(det_labelmap, nii.affine, nii.header)

    return deterministic_nii

def relabel_atlas(labels, labelmap, labels_modules, labelmap_modules_resampled, module_threshold=0):
    """

    Takes 2 atlases, and relabels the first one so that it reflects the modules in the second atlas.

    Parameters:
        labels: Dataframe
            Labelmap labels with their associated region names
        labelmap: str
            Path to labelmap file
        labels_modules: Dataframe
            Resampled modules labelmap labels with their associated module names
        labelmap_modules_resampled: str
            Path to resampled modules labelmap file
        module_threshold: float, optional
            Number between 0 and 1. In the case that a region in 'labelmap' and the background of
            'labelmap_modules_resampled' get the highest similarity score, this threshold will determine if the region
            is considered as not belonging to any modules or as part of the non-background module in
            'labels_modules_resampled'

    Returns:
        reordered_labels: Dataframe
            Reordered labelmap labels with their associated region and module names
        relabelled_labelmap: str
            Path to relabelled labelmap file

    """
    from scipy.spatial.distance import dice
    import nibabel as nb
    import pandas as pd
    import numpy as np
    import heapq
    import time
    import os

    labelmap_nii = nb.load(labelmap)
    labelmap_data = labelmap_nii.get_fdata()
    labelmap_modules_nii = nb.load(labelmap_modules_resampled)
    labelmap_modules_data = labelmap_modules_nii.get_fdata()

    # Reorder labels_modules to ensure that it can be easily compared with the relabelled labelmap
    new_labels_modules = labels_modules
    new_labels_modules['Background'] = np.ones(len(new_labels_modules))
    new_labels_modules['Background'][labels_modules.index.values == 0] = 0
    lut = new_labels_modules.sort_values(by=['Background', 'Region']).reset_index().sort_values(by='Label').index.values
    new_labelmap_modules = lut[np.array(labelmap_modules_data, dtype=np.int32)]
    new_labels_modules = pd.DataFrame({'Module': new_labels_modules['Region']})
    new_labels_modules.index = lut
    new_labels_modules = new_labels_modules.sort_index()
    new_labels_modules = new_labels_modules.rename_axis('Label')

    print(new_labels_modules)

    # Initialize a temporary relabelled_labelmap and modules list
    temp_relabelled_data = np.zeros(labelmap_data.shape)
    modules = ['NA'] * len(labels)
    indices = np.zeros(len(labels))

    for i, lbl in enumerate(labels.index):

        # Get mask of each region in labelmap
        region_mask = np.zeros(labelmap_data.shape)
        region_mask[labelmap_data == lbl] = 1

        # Initialize dice coefficient array
        dice_coeff = np.zeros(len(new_labels_modules))

        # Get dice coefficient of mask overlap with module mask
        for idx, mod in enumerate(new_labels_modules.index):
            # Get mask of each module in labelmap_modules_resampled
            module_mask = np.zeros(labelmap_data.shape)
            module_mask[new_labelmap_modules == mod] = 1

            dice_coeff[idx] = 1 - dice(region_mask.flatten(), module_mask.flatten())

        # Get module (or background) associated to the current
        pos = heapq.nlargest(2, range(len(dice_coeff)), key=dice_coeff.__getitem__)
        val = heapq.nlargest(2, dice_coeff)
        print(val)
        if pos[0] != 0:
            modules[i] = new_labels_modules['Module'][pos[0]]
        elif val[0] < module_threshold:
            modules[i] = new_labels_modules['Module'][pos[1]]

        temp_relabelled_data[labelmap_data == lbl] = i
        indices[i] = i

    # Temporal reordered labels to keep track of changes
    temp_labels = pd.DataFrame({'Region': labels['Region'].tolist(), 'Module': modules}, index=indices)
    temp_labels.index.names = ['Label']
    temp_labels['Network'] = np.ones(len(temp_labels))
    temp_labels['Network'][temp_labels['Module'] == 'NA'] = 0

    # Create final relabelled labelmap using a lookup table to swap labels in the labelmap
    lut = temp_labels.sort_values(by=['Network','Module', 'Region']).reset_index().sort_values(by='Label').index.values
    new_data = lut[np.array(temp_relabelled_data, dtype=np.int32)]

    # Create final reordered_labels
    reordered_labels = temp_labels.filter(['Region','Module'])
    reordered_labels.index = lut
    reordered_labels = reordered_labels.sort_index()
    reordered_labels = reordered_labels.rename_axis('Label')

    # saving relabelled labelmap
    relabelled_labelmap = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),
                            'derivatives/' + time.strftime("%Y%m%d") + '_' + time.strftime("%H%M") + '_relabelled_labelmap_det.nii.gz')
    new_nii = nb.Nifti1Image(new_data, labelmap_nii.affine, labelmap_nii.header)
    nb.save(new_nii, relabelled_labelmap)

    # saving labels as tsv file
    labels_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))),
                               'atlas_files/' + time.strftime("%Y%m%d") + '_' + time.strftime("%H%M") + '_reordered_labels.tsv')
    reordered_labels.to_csv(labels_path, sep="\t")

    return reordered_labels, relabelled_labelmap