


def img_extraction(in_img_4d):
    import os
    import nibabel as nib
    from nilearn.image import index_img

    # Set the Path were the extracted image will be stored
    # img_path = '/home/mo/PycharmProjects/PUMI/data_out/workflow/_subject_001/sub1_img.nii.gz'
    # img_path = '/home/mo/PycharmProjects/PUMI/data_out/workflow/_subject_002/sub2_img.nii.gz'
    img_path = '/home/mo/PycharmProjects/PUMI/data_out/workflow/_subject_003/sub3_img.nii.gz'

    # Store the first slice of the 4d image in order to get a 3d image.
    nib.save(index_img(in_img_4d, 0), img_path)
    return img_path


