import os
import pandas as pd
import numpy as np
from nilearn.connectome import ConnectivityMeasure
from sklearn.preprocessing import StandardScaler


def scrub(ts, fd, scrub_threshold, frames_before=0, frames_after=0):
    frames_out = np.argwhere(fd > scrub_threshold).flatten().tolist()
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
            if i+count < len(fd):  # do not censor unexistent data
                extra_indices.append(i + count)
            count += 1

    indices_out = list(set(frames_out) | set(extra_indices))
    indices_out.sort()

    return np.delete(ts, indices_out, axis=0)


def load_timeseries(ts_files, data_frame, scrubbing=True, scrub_threshold=0.15):
    timeseries = []
    perc_scrubbed = []
    for i, f in enumerate(ts_files):
        ts = pd.read_csv(f, sep="\t").values

        fd = pd.read_csv(data_frame["fd_file"].values.ravel()[i]).values.ravel().tolist()
        fd = [0] + fd
        if scrubbing:
            ts = scrub(ts, np.array(fd), scrub_threshold)

        perc_scrubbed.append(100 - 100*len(ts[:, 1])/len(fd))

        ts = StandardScaler().fit_transform(ts)
        timeseries.append(ts)

    data_frame['perc_scrubbed'] = perc_scrubbed
    data_frame['ts_file'] = ts_files

    labels = pd.read_csv(ts_files[0], sep="\t").columns

    return timeseries, labels


def connectivity_matrix(timeseries, kind='partial correlation'):
    # timeseries: as output by load_timeseries
    correlation_measure = ConnectivityMeasure(kind=kind, vectorize=True, discard_diagonal=True)
    correlation_matrix = correlation_measure.fit_transform(timeseries)
    return correlation_matrix, correlation_measure
