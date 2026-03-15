
def mist_modules(mist_directory, resolution="122"):
    """
       Return a list of the modules contained in the MIST atlas
       Parameters:
           mist_directory (str): Path to the MIST directory
           resolution (str): Resolution (you have to check which resolutions are valid)
       Returns:
           result ([str]): A list containing the modules in the MIST atlas
    """

    import pandas as pd

    resolution = 's' + resolution
    mist_hierarchy_filename = mist_directory + '/' + 'Hierarchy/MIST_PARCEL_ORDER_ROI.csv'
    mist_hierarchy = pd.read_csv(mist_hierarchy_filename, sep=",")
    mist_hierarchy_res = mist_hierarchy[(resolution)]
    mist_hierarchy_res = mist_hierarchy_res.drop_duplicates()

    modul_indices = mist_hierarchy.loc[mist_hierarchy_res.index.values, ['s7', resolution]].sort_values(by=resolution)['s7']
    mist_s7_filename = mist_directory + '/' + 'Parcel_Information/MIST_7.csv'
    mist_s7 = pd.read_csv(mist_s7_filename, sep=";")

    labels = mist_s7.loc[modul_indices-1, ['roi', 'label']].reset_index()
    result = labels['label'].values.tolist()
    return result


def mist_labels(mist_directory, resolution="122"):
    """
       Return a list of the labels contained in the MIST atlas
       Parameters:
           mist_directory (str): Path to the MIST directory
           resolution (str): Resolution (you have to check which resolutions are valid)
       Returns:
           result ([str]): A list containing the labels in the MIST atlas
    """

    import pandas as pd

    mist_filename = mist_directory + '/' + 'Parcel_Information/MIST_' + resolution + '.csv'

    mist = pd.read_csv(mist_filename, sep=";")
    result = mist['label'].values.tolist()
    return result


def relabel_atlas(atlas_file, modules, labels):
    """
       Relabel atlas
       * Beware : currently works only with labelmap!!
       Parameters:
           atlas_file(str): Path to the atlas file
           modules ([str]): List containing the modules in MIST
           labels ([str]): List containing the labels in MIST
       Returns:
           relabel_file (str): Path to relabeld atlas file
           reordered_modules ([str]): list containing reordered module names
           reordered_labels ([str]): list containing reordered label names
           new_labels (str): Path to .tsv-file with the new labels
    """

    import os
    import numpy as np
    import pandas as pd
    import nibabel as nib

    df = pd.DataFrame({'modules': modules, 'labels': labels})
    df.index += 1  # indexing from 1

    reordered = df.sort_values(by='modules')

    # relabel labelmap
    img = nib.load(atlas_file)
    if len(img.shape) != 3:
        raise Exception("relabeling does not work for probability maps!")

    lut = reordered.reset_index().sort_values(by="index").index.values + 1
    lut = np.array([0] + lut.tolist())
    # maybe this is a bit complicated, but believe me it does what it should

    data = img.get_fdata()
    newdata = lut[np.array(data, dtype=np.int32)]  # apply lookup table to swap labels

    img = nib.Nifti1Image(newdata.astype(np.float64), img.affine)
    nib.save(img, 'relabeled_atlas.nii.gz')

    out = reordered.reset_index()
    out.index = out.index + 1
    relabel_file = os.path.join(os.getcwd(), 'relabeled_atlas.nii.gz')
    reordered_modules = reordered['modules'].values.tolist()
    reordered_labels = reordered['labels'].values.tolist()

    newlabels_file = os.path.join(os.getcwd(), 'newlabels.tsv')
    out.to_csv(newlabels_file, sep='\t')
    return relabel_file, reordered_modules, reordered_labels, newlabels_file


def relabel_mist_atlas(atlas_file, modules, labels):
    """
       Relabel MIST atlas
       * Beware : currently works only with labelmap!!
       Parameters:
           atlas_file(str): Path to the atlas file
           modules ([str]): List containing the modules in MIST
           labels ([str]): List containing the labels in MIST
       Returns:
           relabel_file (str): Path to relabeld atlas file
           reordered_modules ([str]): list containing reordered module names
           reordered_labels ([str]): list containing reordered label names
           new_labels (str): Path to .tsv-file with the new labels
    """

    import os
    import numpy as np
    import pandas as pd
    import nibabel as nib

    df = pd.DataFrame({'modules': modules, 'labels': labels})
    df.index += 1  # indexing from 1

    reordered = df.sort_values(by='modules')

    # relabel labelmap
    img = nib.load(atlas_file)
    if len(img.shape) != 3:
        raise Exception("relabeling does not work for probability maps!")

    lut = reordered.reset_index().sort_values(by="index").index.values + 1
    lut = np.array([0] + lut.tolist())
    # maybe this is a bit complicated, but believe me it does what it should

    data = img.get_fdata()
    newdata = lut[np.array(data, dtype=np.int32)]  # apply lookup table to swap labels

    img = nib.Nifti1Image(newdata.astype(np.float64), img.affine)
    nib.save(img, 'relabeled_atlas.nii.gz')

    out = reordered.reset_index()
    out.index = out.index + 1
    relabel_file = os.path.join(os.getcwd(), 'relabeled_atlas.nii.gz')
    reordered_modules = reordered['modules'].values.tolist()
    reordered_labels = reordered['labels'].values.tolist()

    newlabels_file = os.path.join(os.getcwd(), 'newlabels.tsv')
    out.to_csv(newlabels_file, sep='\t')
    return relabel_file, reordered_modules, reordered_labels, newlabels_file
