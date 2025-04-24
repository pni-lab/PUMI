def TsExtractor(labels, labelmap, func, mask, global_signal=True, pca=False, outfile="reg_timeseries.tsv",
                outlabelmap="individual_gm_labelmap.nii.gz"):
    # todo: check method
    import os
    import nibabel as nib
    import numpy as np
    import pandas as pd

    func_data = nib.load(func).get_fdata()
    labelmap_data = nib.load(labelmap).get_fdata()
    mask_data = nib.load(mask).get_fdata()

    labelmap_data[mask_data==0] = 0 # background

    outlab = nib.Nifti1Image(labelmap_data, nib.load(labelmap).affine)
    nib.save(outlab, outlabelmap)

    ret = []

    if global_signal:
        indices = np.argwhere(mask_data > 0)
        X = []
        for i in indices:
            x = func_data[i[0], i[1], i[2], :]
            if np.std(x) > 0.000001:
                X.append(x.tolist())
        if len(X) == 0:
            x = np.repeat(0, func_data.shape[3])
        elif pca:
            import sklearn.decomposition as decomp
            from sklearn.preprocessing import StandardScaler
            X = StandardScaler().fit_transform(np.transpose(X))
            PCA = decomp.PCA(n_components=1, svd_solver="arpack")
            x = PCA.fit_transform(X).flatten()
        else:
            x = np.mean(X, axis=0)
        ret.append(x)

    for l in range(1,len(labels)+1):
        indices=np.argwhere(labelmap_data == l)
        X = []
        for i in indices:
            x = func_data[i[0], i[1], i[2], :]
            if np.std(x) > 0.000001:
                X.append(x.tolist())
        X = np.array(X)
        if X.shape[0]==0:
            x=np.repeat(0,func_data.shape[3])
        elif X.shape[0]==1:
            x=X.flatten()
        elif pca:
            import sklearn.decomposition as decomp
            from sklearn.preprocessing import StandardScaler
            X = StandardScaler().fit_transform(np.transpose(X))
            PCA = decomp.PCA(n_components=1, svd_solver="arpack")
            x = PCA.fit_transform(X).flatten()
        else:
            x = np.mean(X, axis=0)
        ret.append(x)

    ret = np.transpose(np.array(ret))

    if global_signal:
        labels = ["GlobSig"] + labels

    ret = pd.DataFrame(data=ret, columns=labels)

    ret.to_csv(outfile, sep="\t", index=False)

    return os.path.join(os.getcwd(), outfile), labels, os.path.join(os.getcwd(), outlabelmap)


def get_indx(scrub_input, frames_in_1D_file):
    """

    Method to get the list of time
    frames that are to be included

    Parameters:
        in_file (str): path to file containing the valid time frames

    Returns:
        scrub_input_string (str): input string for 3dCalc in scrubbing workflow,
                              looks something like " 4dfile.nii.gz[0,1,2,..100] "
    """

    frames_in_idx_str = '[' + ','.join(str(x) for x in frames_in_1D_file) + ']'
    scrub_input_string = scrub_input + frames_in_idx_str

    return scrub_input_string



def above_threshold(in_file, threshold=0.2, frames_before=1, frames_after=2):

    """

        todo docs

    """

    import os
    import numpy as np
    from numpy import loadtxt, savetxt

    powersFD_data = loadtxt(in_file, skiprows=1)
    np.insert(powersFD_data, 0, 0)  # TODO_ready: why do we need this: see output of nipype.algorithms.confounds.FramewiseDisplacement
    frames_in_idx = np.argwhere(powersFD_data < threshold)[:, 0]
    frames_out = np.argwhere(powersFD_data >= threshold)[:, 0]

    extra_indices = []
    for i in frames_out:

        # remove preceding frames
        if i > 0:
            count = 1
            while count <= frames_before:
                extra_indices.append(i - count)
                count += 1

        # remove following frames
        count = 1
        while count <= frames_after:
            if i+count < len(powersFD_data):  # do not censor unexistent data
                extra_indices.append(i + count)
            count += 1
    indices_out = list(set(frames_out) | set(extra_indices))
    indices_out.sort()

    frames_out_idx = indices_out
    frames_in_idx = np.setdiff1d(frames_in_idx, indices_out)

    FD_scrubbed = powersFD_data[frames_in_idx]
    fd_scrubbed_file = os.path.join(os.getcwd(), 'FD_scrubbed.csv')
    savetxt(fd_scrubbed_file, FD_scrubbed, delimiter=",")

    frames_in_idx_str = ','.join(str(x) for x in frames_in_idx)
    frames_in_idx = frames_in_idx_str.split()

    percentFD = (len(frames_out_idx) * 100 / (len(powersFD_data) + 1)) # % of frames censored
    percent_scrubbed_file = os.path.join(os.getcwd(), 'percent_scrubbed.txt')
    f = open(percent_scrubbed_file, 'w')
    f.write("%.3f" % (percentFD))
    f.close()

    nvol = len(powersFD_data)

    return frames_in_idx, frames_out_idx, percentFD, percent_scrubbed_file, fd_scrubbed_file, nvol

def concatenate(fname='parfiles.txt', **pars):

    """

    todo Docs

    """
    import os
    import numpy as np

    par_files = list(pars.values())

    totpar = np.loadtxt(par_files[0])
    for idx in range(1, len(par_files)):
        if par_files[idx] is None:
            continue
        tmp = np.loadtxt(par_files[idx])
        totpar = np.concatenate((totpar, tmp), axis=1)
        if fname.startswith('/'):
            path = fname
        else:
            path = os.path.join(os.getcwd(), fname)
    np.savetxt(path, totpar)
    return path

def plot_carpet_ts(timeseries, modules, atlas=None, background_file=None, subplot=None, output_file="regts.png"):
    """
    Adapted from: https://github.com/poldracklab/niworkflows
    Plot an image representation of voxel intensities across time also know
    as the "carpet plot" or "Power plot". See Jonathan Power Neuroimage
    2017 Jul 1; 154:150-158.
    Parameters:
        timeseries (numpy.ndarray): 4D input image. See http://nilearn.github.io/manipulating_images/input_output.html.
        output_file (str, None): Optional! The name of the output image. Valid extensions are .png, .pdf, .svg.
    """
    import numpy as np
    import nibabel as nb
    import pandas as pd
    import os
    import matplotlib.pyplot as plt
    from matplotlib import gridspec as mgs
    import matplotlib.cm as cm
    from matplotlib.colors import ListedColormap
    from nilearn.plotting import plot_img

    legend = False
    if atlas:
        legend = True

    # actually load data
    timeseries = pd.read_csv(timeseries, sep="\t")

    #normalise all timeseries
    v = (None, None)
    timeseries = (timeseries - timeseries.mean()) / timeseries.std()
    v = (-2, 2)
    timeseries = timeseries.transpose()

    minimum = timeseries.min()
    maximum = timeseries.max()
    myrange = maximum - minimum

    modules = pd.Series(modules).values
    lut = pd.factorize(modules)[0]+1

    # If subplot is not defined
    if subplot is None:
        subplot = mgs.GridSpec(1, 1)[0]

    # Define nested GridSpec
    wratios = [2, 120, 20]
    gs = mgs.GridSpecFromSubplotSpec(1, 2 + int(legend), subplot_spec=subplot,
                                     width_ratios=wratios[:2 + int(legend)],
                                     wspace=0.0)

    mycolors = ListedColormap(cm.get_cmap('Set1').colors[:7][::-1])

    # Segmentation colorbar

    ax0 = plt.subplot(gs[0])

    ax0.set_yticks([])
    ax0.set_xticks([])

    lutt=pd.DataFrame({'1': lut})
    ax0.imshow(lutt, interpolation='none', aspect='auto',
               cmap=mycolors, vmin=0, vmax=8)

    ax0.grid(False)
    ax0.spines["left"].set_visible(False)
    ax0.spines["bottom"].set_color('none')
    ax0.spines["bottom"].set_visible(False)


    # Carpet plot
    ax1 = plt.subplot(gs[1])
    ax1.imshow(timeseries, interpolation='nearest', aspect='auto', cmap='gray',
               vmin=v[0], vmax=v[1])

    ax1.grid(False)
    ax1.set_yticks([])
    ax1.set_yticklabels([])

    # Set 10 frame markers in X axis
    interval = max((int(timeseries.shape[-1] + 1) // 10, int(timeseries.shape[-1] + 1) // 5, 1))
    xticks = list(range(0, timeseries.shape[-1])[::interval])
    ax1.set_xticks(xticks)
    ax1.set_xlabel('time')

    # Remove and redefine spines
    for side in ["top", "right"]:
        # Toggle the spine objects
        ax0.spines[side].set_color('none')
        ax0.spines[side].set_visible(False)
        ax1.spines[side].set_color('none')
        ax1.spines[side].set_visible(False)

    ax1.yaxis.set_ticks_position('left')
    ax1.xaxis.set_ticks_position('bottom')
    ax1.spines["bottom"].set_visible(False)
    ax1.spines["left"].set_color('none')
    ax1.spines["left"].set_visible(False)

    if legend:
        gslegend = mgs.GridSpecFromSubplotSpec(
            5, 1, subplot_spec=gs[2], wspace=0.0, hspace=0.0)

        if not background_file:
            background_file = atlas #TODO: works only for 3mm atlas
        background = nb.load(background_file)
        atlas = nb.load(atlas)

        nslices = background.shape[-1]
        coords = [-40, 20, 0, 20, 40]  # works in MNI space
        lut2 = lut
        lut2 = np.array([0] + lut2.tolist())

        relabeled=lut2[np.array(atlas.get_fdata(), dtype=int)]
        atl = nb.Nifti1Image(relabeled, atlas.affine, dtype=np.int64)
        for i, c in enumerate(coords):
            ax2 = plt.subplot(gslegend[i])
            plot_img(atl, bg_img=background, axes=ax2, display_mode='z',
                     annotate=False, cut_coords=[c], threshold=0.1, cmap=mycolors,
                     interpolation='nearest', vmin=1, vmax=7)

    if output_file is not None:
        figure = plt.gcf()
        figure.savefig(output_file, bbox_inches='tight')
        plt.close(figure)
        figure = None
        return os.getcwd() + '/' + output_file

    return [ax0, ax1], gs


