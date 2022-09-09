def plot_carpet(img, mask=None, output_file=None, save_carpet=False, cmap='gray',
                detrend=True, standardize='zscore',
                clean_data=True, show_carpet=False):
    """
    Adapted from: https://github.com/poldracklab/niworkflows
    Plot an image representation of voxel intensities across time also known
    as the "carpet plot" or "Power plot". See Jonathan Power Neuroimage
    2017 Jul 1; 154:150-158.

    - X-axis: timeframes (bottom to top along z axis).
    - Y-axis: voxels.
    - Color: voxel intensity.

    Parameters:
        img (Niimg-like object):
            4D functional image.
        mask (3d binary image (brain mask) or a float between 0 and 1):
            Fractional intensity threshold, i.e. ignoring all voxels being smaller than the min+mask*(max-min).
            Default = 0.1
        cmap (str) :
            The color map that will be used to color the carpet.
            Default = 'gray'
        detrend (bool) :
            Weather data will be detrended or not. Default = True
        standardize :{'zscore', 'psc', False}.
            Strategy to standardize the signal. Default = 'zscore'
        clean_data (bool):
            Remove voxels that stay 0 through time.
            Default = True.
        show_carpet (bool):
            Show the generated carpet plot after generating it.
        output_file (str):
            Absolute Path in which the carpet plot should be saved
            If the value is None, carpet will be stored in the cwd.
        save_carpet (bool):
            Save generated carpet in the path output_file.
            In case output_file is None: carpet will be stored in the current working directory.
            Note: if output_file was provide save_carpet will be set to True automatically.

    Returns:
        Matplotlib Axes: The plot itself.


    """
    import numpy as np
    import nibabel as nb
    import matplotlib.pyplot as plt
    from matplotlib import gridspec as mgs
    from nilearn._utils import check_niimg_4d
    from nilearn._utils.niimg import _safe_get_data
    from nilearn.signal import clean
    import os

    # actually load data
    print(img)
    img_name = img.split('/')[-1]
    img = nb.load(img)

    img_nii = check_niimg_4d(img, dtype='auto')
    func_data = _safe_get_data(img_nii, ensure_finite=True)  # Get data from the image

    minimum = np.min(func_data)
    maximum = np.max(func_data)
    myrange = maximum - minimum
    np.set_printoptions(threshold=1981981)

    # Define TR(Time of Repation) and number of frames
    # Time between collecting a slice in one volume, and that same slice in the next one
    tr = img_nii.header.get_zooms()[-1]

    ntsteps = func_data.shape[-1]  # get number of timeframes.
    # Convert func_data from 4d Array to 2d
    # in the second dim there will be ntsteps(timeframes) items.
    data_2d = func_data.reshape(-1, ntsteps)  # changes for each voxel through all timeframes.
    voxels_count = data_2d.shape[0]

    # Check if a mask was given as parameter
    if type(mask) == np.ndarray:
        if len(mask.shape) != 3:
            raise ValueError('Mask has to be 3 dimensional')
        if func_data.shape[:3] != mask.shape:
            raise ValueError('fMRI and mask must be in the same space!')
        reshaped_mask = mask.reshape(-1)  # From 3d to 1d
        for n in range(ntsteps):
            data_2d[:, n] = data_2d[:,
                            n] * reshaped_mask  # multiply 3d images with mask one at a time
    else:
        if mask is None:
            mask = 0.1
        if 0 > mask or mask > 1:
            raise ValueError('Mask can only be a 3d binary image or a float between 0 and 1.')
        data_2d = func_data.reshape(-1, ntsteps)  # changes for each voxel through all timeframes.
        threshhold = int(minimum + mask * (maximum - minimum))
        mask = np.array(data_2d > threshhold, dtype=int)
        data_2d = data_2d * mask  # apply mask



    # Remove voxels which are 0 throughout all time-points
    if clean_data:
        # print('Data shape before cleaning : ', data_2d.shape)
        data_2d = np.array(
            [x for x in data_2d if x.nonzero()[0].size != 0])
        # print('Data shape before cleaning :', data_2d.shape)



    subplot = mgs.GridSpec(1, 2)[0:]
    wratios = [1, 100, 20]
    gs = mgs.GridSpecFromSubplotSpec(1, 2, subplot_spec=subplot,
                                     width_ratios=wratios[:2],  # size of the columns
                                     wspace=0.0)


    # Detrend data
    v = (None, None)
    if detrend:
        data_2d = clean(data_2d.T, t_r=tr, standardize=standardize).T  # T = Transform of the array
        v = (-2, 2)

    # Carpet plot
    ax1 = plt.subplot(gs[1])
    # print('There are {} Voxels and {} timeframes(Volumes).'.format(voxels_count, ntsteps))
    ax1.imshow(data_2d, aspect='auto', cmap=cmap, interpolation='nearest',
               vmin=v[0], vmax=v[1])
    ax1.annotate(
        'intensity range: ' + str(myrange), xy=(0.0, 1.02), xytext=(0, 0), xycoords='axes fraction',
        textcoords='offset points', va='center', ha='left',
        color='r', size=6,
        bbox={'boxstyle': 'round', 'fc': 'w', 'ec': 'none',
              'color': 'none', 'lw': 0, 'alpha': 0.0})

    # Set 10 frame markers in X axis
    interval = max((int(data_2d.shape[-1] + 1) // 10, int(data_2d.shape[-1] + 1) // 5, 1))
    xticks = list(range(0, data_2d.shape[-1] + 1)[0:ntsteps + 1:interval])
    ax1.set_xticks(xticks)
    ax1.set_xlabel('time (s)')
    labels = tr * (np.array(xticks))
    ax1.set_xticklabels(['%.02f' % t for t in labels.tolist()], fontsize=5)




    output_file = os.path.join(os.path.dirname(os.getcwd()), img_name + '_carpet.png') if output_file is None \
        else os.path.join(output_file, img_name + '_carpet.png')

    fig = plt.gcf()
    if save_carpet or output_file is not None:
        print('Carpet will be saved in ', output_file)
        fig.savefig(output_file)


    if show_carpet:
        plt.show()

    plt.close(fig)

    return ax1


if __name__ == '__main__':
    import os
    from numpy import random

    # Test Mask
    arr = random.randint(2, size=(94, 94, 38))
    ROOT_DIR = os.path.dirname(os.getcwd())
    input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
    plot_carpet(os.path.join(input_dir, 'sub-001/func/sub-001_task-rest_bold.nii.gz'),
                save_carpet=True, show_carpet=False, mask=arr)
    '''
    # Test default mask (default mask = 0.1)
    arr = random.randint(2, size=(94, 94, 38))
    ROOT_DIR = os.path.dirname(os.getcwd())
    input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
    plot_carpet(os.path.join(ROOT_DIR, input_dir, 'sub-001/func/sub-001_task-rest_bold.nii.gz'))
    '''
