from multiprocessing.managers import Value
from pathlib import Path

from sklearn.feature_selection import SelectKBest
from sklearn.linear_model import ElasticNet
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.feature_selection import f_regression
from templateflow import api as tflow
import numpy as np
import json
import os





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

def rpn_model(file):
    with open(file, 'r') as f_obj:
        data = json.load(f_obj)
    pipeline_steps = []

    # *** RobustScaler ***
    scaler = RobustScaler(**data['RobustScaler']['init_params'])
    center_ = np.array(data['RobustScaler']['model_params']['center_'])
    scale_ = np.array(data['RobustScaler']['model_params']['scale_'])
    setattr(scaler, 'center_', center_)
    setattr(scaler, 'scale_', scale_)
    pipeline_steps.append(('scaler', scaler))

    # *** SelectKBest ***
    data['SelectKBest']['init_params']['score_func'] = f_regression
    fsel = SelectKBest(**data['SelectKBest']['init_params'])
    scores_ = np.array(data['SelectKBest']['model_params']['scores_'])
    pvalues_ = np.array(data['SelectKBest']['model_params']['pvalues_'])
    setattr(fsel, 'scores_', scores_)
    setattr(fsel, 'pvalues_', pvalues_)
    pipeline_steps.append(('fsel', fsel))

    # *** ElasticNet ***
    model = ElasticNet(**data['ElasticNet']['init_params'])
    coef_ = np.array(data['ElasticNet']['model_params']['coef_'])
    #sparse_coef_ = csr_matrix(data['ElasticNet']['model_params']['sparse_coef_'])
    intercept_ = data['ElasticNet']['model_params']['intercept_']
    n_iter_ = data['ElasticNet']['model_params']['n_iter_']
    dual_gap_ = np.array(data['ElasticNet']['model_params']['dual_gap_'])
    setattr(model, 'coef_', coef_)
    # setattr(step, 'sparse_coef_', sparse_coef_)
    setattr(model, 'intercept_', intercept_)
    setattr(model, 'n_iter_', n_iter_)
    setattr(model, 'dual_gap_', dual_gap_)
    pipeline_steps.append(('model', model))
    return Pipeline(pipeline_steps)