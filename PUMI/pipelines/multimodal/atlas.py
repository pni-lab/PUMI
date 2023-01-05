from PUMI.engine import GroupPipeline
from nilearn.datasets import atlas as nlatlas
from fnmatch import fnmatch
import numpy as np
import pandas as pd
import nibabel as nib
import os

def fetch_atlas(atlasname, atlas_dir=None, **kwargs):
    """
    Determines which atlas to fetch.

        Parameters
        ----------
        atlasname : str or list
            Input string can be for: 'aal,'destrieux','difumo','harvard_oxford','juelich','msdl',
                                     'MIST','pauli','schaefer','talairach','yeo'
        atlas_dir : str, optional
            Path to a custom atlas labelmap and label text file.

        Note: **kwargs is not available for the `destrieux` atlas.

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

    # get atlas
    if not atlas_dir:
        if atlasname == 'MIST':
            mist_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "../data_in/atlas/MIST"))
            labelmap_dir = mist_dir + '/Parcellations/MIST_' + kwargs['resolution'] + '.nii.gz'
            labelmap = nib.load(labelmap_dir)
            labels_dir = mist_dir + '/Parcel_Information/MIST_' + kwargs['resolution'] + '.csv'
            labels = pd.read_csv(labels_dir, delimiter=";")
            labels = labels['label'].values.tolist()
        else:
            function_name = [x for x in dir(nlatlas) if fnmatch(x, "fetch_atlas_" + atlasname + "*")]
            if function_name:
                function_name = str(function_name[0])
                atlas_function = getattr(nlatlas, function_name)
                if atlasname in {'destrieux','difumo'}:
                    kwargs = {'legacy_format':False}

                if kwargs and atlasname != 'yeo':
                    atlas = atlas_function(**kwargs)
                else:
                    atlas = atlas_function()

                if atlasname == 'yeo':
                    labelmap = atlas[kwargs['key']]
                    if '17' in kwargs['key']:
                        labels = pd.read_csv(atlas['colors_17'], sep=r'\s+')['NONE'].tolist()
                    else:
                        labels = pd.read_csv(atlas['colors_7'], sep=r'\s+')['NONE'].tolist()
                else:
                    labelmap = atlas['maps']
                    labels = atlas['labels']
                    if atlasname == 'schaefer':
                        labels = np.insert(atlas['labels'], 0, 'Background')
            else:
                raise ValueError('No atlas detected. Check query string')
    else:
        if os.path.exists(atlas_dir):
            labelmap = atlas_dir + '/Parcellations/' + atlasname + '.nii.gz'
            labels_file = atlas_dir + '/Parcel_information/' + atlasname + '.csv'
            labels = pd.read_csv(labels_file, sep=";")
            labels = labels.values.tolist()
        else:
            raise ValueError('No atlas detected. Check query or atlas directory')

    labels_out = os.path.join(os.getcwd(), atlasname + 'newlabels.tsv')
    if isinstance(labels, pd.DataFrame):
        labels = labels.values.tolist()

    df = pd.DataFrame({'Labels': labels})
    if atlasname == 'aal':
        df.index = atlas['indices'] # corresponding to region IDs
    else:
        df.index += 1  # indexing from 1
    df.to_csv(labels_out,sep='\t')
    print(df.head())

    return labelmap, labels