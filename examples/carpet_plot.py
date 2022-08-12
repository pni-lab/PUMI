# A Voxel in 3d is like a pixel in 2d

# a volume is a single 3D representation of brain data

# size : Maximum number of samples to plot (voxels, timepoints)

# Axis starts from 0 so if axis = 0 we are talking about the dim-1 of a np-array

# The time between repeated volumes (i.e., between collecting a slice in one volume, and that same slice in the next) is the TR (repetition time).

# The variable lut is supposed to be a lookup table

# Ticks are the numbers on the axis

# Spines are the borders of a graph

# 0 Black ---> 255 white
# A Voxel in 3d is like a pixel in 2d
# The variable lut is supposed to be a lookup table

# if vmax was reached set maximum of cmap as color(white)
# if it is smaller than vmin set color minimum(black)
# Values betweeen the limits will be mapped to the different colors of the cmap with respect to their size.
# ax1.imshow(data, interpolation='nearest', aspect='auto', cmap='gray', vmin=0, vmax=400)

'''
    - This 4d-image contains 290 volumes
    - Each Volume(3d Image) contains 38 Slices(2d Images)
    - Each Slice is 94 x 94 Pixel
    So there are 94*94*38=335768 Rows and 290 Columns.
    For example the whole first column represents the all pixels of the first volume

    one_vol = func_data[..., 150]
    one_slice = one_vol[..., 15]
'''

'''
INPUT:
take a 4D functional image as input
optional argument: 'mask', this can be a 3d binary image (brain mask) or a float between 0 and 1 (default: 0.1), which is a "fractional intensity threshold", i.e. ignoring all voxels being smaller than the min+mask*(max-min) (or something like that)
additional params: ax: matplotlib axis, for composite figure (optional), cmap: matplotlib-like colormap (default: grayscale)
The function plots all within-mask voxels as a "carpet image":
y axis: voxels (bottom to top along z axis)
x axis. timeframes
color: voxel intensity
returns:
the plot itself (matplotlib axis)
'''

import os
from numpy import random


def plot_carpet(img, mask=None, cmap='gray', detrend=True):
    """
    Adapted from: https://github.com/poldracklab/niworkflows
    Plot an image representation of voxel intensities across time also know
    as the "carpet plot" or "Power plot". See Jonathan Power Neuroimage
    2017 Jul 1; 154:150-158.
    Parameters
    ----------
        img : Niimg-like object
            See http://nilearn.github.io/manipulating_images/input_output.html0
            4D input image
        axes : matplotlib axes, optional
            The axes used to display the plot. If None, the complete
            figure is used.
        output_file : string, or None, optional
            The name of an image file to export the plot to. Valid extensions
            are .png, .pdf, .svg. If output_file is not None, the plot
            is saved to a file, and the display is closed.
    """
    import numpy as np
    import nibabel as nb
    import matplotlib.pyplot as plt
    from matplotlib import gridspec as mgs
    import matplotlib.cm as cm
    from matplotlib.colors import ListedColormap
    from nilearn.plotting import plot_img
    from nilearn._utils import check_niimg_4d
    from nilearn._utils.niimg import _safe_get_data
    from nilearn.signal import clean

    # actually load data
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
    threshhold = 0
    if type(mask) == np.ndarray:
        if len(mask.shape) != 3:
            raise ValueError('Mask has to be 3 dimensional')
        if func_data.shape[:3] != mask.shape:
            raise ValueError('fMRI and mask must be in the same space!')
        reshaped_mask = mask.reshape(-1)  # From 3d to 1d
        for n in range(ntsteps):
            data_2d[:, n] = data_2d[:,
                            n] * reshaped_mask  # multiply columns(flattened 3d images at one time-point) with mask one at a time
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
    print('Data shape before cleaning : ', data_2d.shape)
    data_2d = np.array(
        [x for x in data_2d if x.nonzero()[0].size != 0])
    print('Cleaned Data Shape : ', data_2d.shape)

    subplot = mgs.GridSpec(1, 2)[0:]
    wratios = [1, 100, 20]
    gs = mgs.GridSpecFromSubplotSpec(1, 2, subplot_spec=subplot,
                                     width_ratios=wratios[:2],  # size of the columns
                                     wspace=0.0)

    # Detrend data
    v = (None, None)
    if detrend:
        data_2d = clean(data_2d.T, t_r=tr).T # T = Transform of the array
        v = (-2, 2)

    # Carpet plot
    ax1 = plt.subplot(gs[1])
    print('There are {} Voxels and {} timeframes(Volumes).'.format(voxels_count, ntsteps))
    ax1.imshow(data_2d[:, ...], aspect='auto', cmap=cmap, interpolation='nearest',
               vmin=v[0], vmax=v[1])  # voxels will start from <threshhold> because of mask
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

    plt.show()
    return ax1


if __name__ == '__main__':
    # Test Mask
    arr = random.randint(2, size=(94, 94, 38))
    ROOT_DIR = os.path.dirname(os.getcwd())
    input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
    plot_carpet(os.path.join(ROOT_DIR, input_dir, 'sub-001/func/sub-001_task-rest_bold.nii.gz'), mask=arr)
    '''
    # Test no mask (default mask = 0.1)
    arr = random.randint(2, size=(94, 94, 38))
    ROOT_DIR = os.path.dirname(os.getcwd())
    input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
    plot_carpet(os.path.join(ROOT_DIR, input_dir, 'sub-001/func/sub-001_task-rest_bold.nii.gz'))
    '''