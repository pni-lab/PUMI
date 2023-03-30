import pandas as pd
import numpy as np
from nilearn.connectome import ConnectivityMeasure
from sklearn.preprocessing import StandardScaler
from matplotlib.colors import Normalize
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
import seaborn as sns
from nilearn import plotting


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


class MidpointNormalize(Normalize):
    def __init__(self, vmin=None, vmax=None, midpoint=None, clip=False):
        self.midpoint = midpoint
        Normalize.__init__(self, vmin, vmax, clip)

    def __call__(self, value, clip=None):
        # I'm ignoring masked values and all kinds of edge cases to make a
        # simple example...
        x, y = [self.vmin, self.midpoint, self.vmax], [0, 0.5, 1]
        return np.ma.masked_array(np.interp(value, x, y))


def plot_matrix(mat, labels, modules, outfile="", zero_diag=True):
    # plot group-mean matrix
    norm = MidpointNormalize(midpoint=0)

    if zero_diag:
        mat[range(mat.shape[0]), range(mat.shape[0])] = 0

    plotting.plot_matrix(mat, labels=labels.tolist(), auto_fit=True, norm=norm,
                         cmap=ListedColormap(sns.diverging_palette(220, 15, sep=1, n=31)), figure=(10, 10))

    prev=""
    idx=0
    for i in range(len(labels)):
        if modules[i]!=prev:
            plt.plot([-5, len(labels) + 0.5], [i-0.5, i-0.5], linewidth=1, color='gray')
            plt.plot([i - 0.5, i - 0.5], [-5, len(labels) + 0.5], linewidth=1, color='gray')

            idx=idx+1
            prev=modules[i]

    if outfile:
        figure = plt.gcf()
        figure.savefig(outfile, bbox_inches='tight')
        plt.close(figure)
    else:
        plotting.show()