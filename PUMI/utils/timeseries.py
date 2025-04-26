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
