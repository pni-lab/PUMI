def fetch_atlas(name_atlas, atlas_dir=None, **kwargs):
    """
    Determines which atlas to fetch.

        Parameters
        ----------
        name_atlas : str or list
            Input string can be for: 'aal,'destrieux','difumo','harvard_oxford','juelich','msdl',
                                     'MIST','pauli','schaefer','talairach','yeo'
        atlas_dir : str, optional
            Path to a custom atlas labelmap and label text file.

        Note: **kwargs is not available for the `destrieux` atlas.

        Returns
        -------
        dataframe or None
            The atlas labelmap and the accompanying labels

        Raises
        ------
        ValueError
            Raised when the atlas is not formatted correctly or if there is no
            match found.
        """
    import numpy as np
    import pandas as pd
    import os

    print(kwargs)
    if kwargs:
        map_args = kwargs['atlas_args']
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
        from nilearn.datasets import atlas as nl_atlas
        from fnmatch import fnmatch

        # Obtain the name of the nilearn atlas function
        function_name = [x for x in dir(nl_atlas) if fnmatch(x, "fetch_atlas_" + name_atlas + "*")]

        if function_name:
            # Get atlas
            function_name = str(function_name[0])
            atlas_function = getattr(nl_atlas, function_name)
            atlas = atlas_function(**kwargs)

            # Required considerations for specific atlases
            if name_atlas == 'allen':
                # Get labelmap
                labelmap = atlas['maps']
                # Get indices that map the network names to the map indices
                rsn_ids = atlas['rsn_indices']
                df = pd.DataFrame.from_records(rsn_ids, columns=['Networks', 'Region_id'])
                labels = np.concatenate(atlas['networks'])
                indices = np.concatenate(df['Region_id'])

            elif name_atlas == 'basc':
                # Get labelmap with the specified resolution
                scale = [x for x in dir(atlas) if map_args[0] in x][0]
                labelmap = atlas[scale]
                # Get labels
                mist_dir = os.path.dirname(os.getcwd())+'/data_in/atlas/MIST'
                labels_dir = mist_dir + '/Parcel_Information/MIST_' + map_args[0] + '.csv'
                labels = pd.read_csv(labels_dir, delimiter=";")
                labels = labels['label'].values.tolist()

            elif name_atlas in {'harvard_oxford','juelich'}:
                # Get labelmap and labels
                labelmap = atlas.filename
                labels = atlas['labels']

            elif name_atlas == 'surf_destrieux':
                # Get labelmap of the specified hemisphere
                labelmap = atlas['map_' + map_args[0]]
                # Get labels
                labels = atlas['labels']

            elif name_atlas == 'yeo':
                # Get labelmap
                labelmap = atlas[map_args[0]]
                # Get labels
                if '17' in map_args:
                    # Labels for the 17 Yeo networks
                    labels = ['Visual Central (Visual A)', 'Visual Peripheral (Visual B)', 'Somatomotor A',
                              'Somatomotor B', '	Dorsal Attention A', '	Dorsal Attention B',
                              'Salience / Ventral Attention A', 'Salience / Ventral Attention B',
                              'Limbic A', 'Limbic B', 'Control C', 'Control A', 'Control B', 'Temporal Parietal',
                              'Default C', 'Default A', 'Default B']
                else:
                    # Labels for the 7 Yeo networks
                    labels = ['Visual', 'Somatomotor', 'Dorsal Attention', 'Salience / Ventral Attention',
                              'Limbic', 'Control', 'Default']

            else:
                # Get labelmap and labels
                labelmap = atlas['maps']
                labels = atlas['labels']

                # Add 'Background' label for Schaefer and Pauli's atlases
                if name_atlas in {'schaefer','pauli'}:
                    labels = np.insert(atlas['labels'], 0, 'Background')
                # Convert rec.arrays to DataFrame for DiFuMo and Destrieux atlases
                elif name_atlas in {'difumo', 'destrieux'}:
                    labels = pd.DataFrame.from_records(labels)
                    labels = labels.iloc[:, 1]

        else:
            raise ValueError('No atlas detected. Check query string')

    # Prepare output label file as DataFrame
    output_labels = pd.DataFrame({'Labels': labels})

    # Substitute DataFrame index by region indices for AAL and Allen atlases
    if name_atlas == 'aal':
        output_labels.index = atlas['indices']
    elif name_atlas == 'allen':
        output_labels.index = indices
    # Increase index by 1 unit for atlases without Background label
    elif name_atlas in {'basc','difumo','msdl','yeo'}:
        output_labels.index += 1  # indexing from 1

    # Store label dataframes
    labels_out = os.path.join(os.getcwd(), name_atlas + '_labels.tsv') #os.path.join(os.getcwd(), 'atlas_files/' + name_atlas + '_labels.tsv')
    output_labels.to_csv(labels_out, sep='\t')
    print(output_labels)

    return labels, labelmap