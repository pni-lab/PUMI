from PUMI.engine import GroupPipeline
from nilearn.datasets import atlas as nlatlas
from fnmatch import fnmatch
import numpy as np
import pandas as pd
from PUMI.utils import mist_labels
import os

#@GroupPipeline(inputspec_fields=['atlas_query'],
 #             outputspec_fields=['labels', 'labelmap'])
def fetch_atlas(atlas_query, atlas_dir=None):
    """
    Determines which atlas to fetch and what version of the atlas to use (if applicable).

        Parameters
        ----------
        atlas_query : str or list
            Input string in the following format:
            [atlas_name,atlas_parameters]. The following can be for
            `atlas_name`: 'aal,'destrieux','difumo','harvard_oxford','juelich','msdl','MIST'
                          'pauli','schaefer','talairach','yeo'
            `atlas_parameters` is not available for the `destrieux` atlas.
        atlas_dir : str, optional
            Path to a custom atlas labelmap and label text file.

        Returns
        -------
        str, list or None
            The atlas labelmap and the accompanying labels

        Raises
        ------
        ValueError
            Raised when the atlas is not formatted correctly or if there is no
            match found.
        """
    # extract parameters
    if len(atlas_query) >= 2:
        atlas_name = atlas_query[0]
        sub_param = atlas_query[1:]
    elif len(atlas_query) == 1:
        atlas_name = atlas_query[0]
        sub_param = None
    else:
        raise ValueError('Incorrect query string provided')

    # get atlas
    if not atlas_dir:
        if atlas_name == 'MIST':
            mist_dir = os.path.abspath(os.path.join(os.path.expanduser(os.path.dirname(os.path.dirname(__file__))), "../data_in/atlas/MIST"))
            resolution = sub_param[0]
            labelmap = mist_dir + '/Parcellations/MIST_' + resolution + '.nii.gz'
            labels = mist_labels(mist_dir,resolution=resolution)
        else:
            function_name = [x for x in dir(nlatlas) if fnmatch(x, "fetch_atlas_" + atlas_name + "*")]
            if function_name:
                function_name = str(function_name[0])
                atlas_function = getattr(nlatlas, function_name)
                if sub_param and atlas_name != 'yeo':
                    atlas = atlas_function(*sub_param)
                else:
                    atlas = atlas_function()

                if atlas_name == 'yeo':
                    labelmap = atlas[sub_param[0]]
                    if '17' in sub_param:
                        labels = pd.read_csv(atlas['colors_17'], sep=r'\s+')['NONE'].tolist()
                    else:
                        labels = pd.read_csv(atlas['colors_7'], sep=r'\s+')['NONE'].tolist()
                else:
                    labelmap = atlas['maps']
                    labels = atlas['labels']
                    # labels = labels.astype(str).tolist()
                    if atlas_name == 'schaefer':
                        labels = np.insert(atlas['labels'], 0, 'Background')
            else:
                raise ValueError('No atlas detected. Check query string')
    else:
        if os.path.exists(atlas_dir):
            labelmap = atlas_dir + '/Parcellations/' + sub_param[0] + '.nii.gz'
            labels_file = atlas_dir + '/Parcel_information/' + sub_param[1] + '.csv'
            labels = pd.read_csv(labels_file, sep=";")
            labels = labels.values.tolist()
        else:
            raise ValueError('No atlas detected. Check query or atlas directory')

    return labelmap, labels