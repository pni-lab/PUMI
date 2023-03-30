from PUMI.PAINTeR import plot_matrix
from PUMI.engine import FuncPipeline, NestedNode as Node, QcPipeline
from nilearn.connectome import ConnectivityMeasure
from nipype.interfaces import utility


@FuncPipeline(inputspec_fields=['ts_file', 'fd_file', 'atlas_labels'],
              outputspec_fields=['out_file'])
def create_connectivity_matrix(wf, scrub_threshold=0.15, **kwargs):
    """

    Creates connectivity matrix and qc image

    Parameters:
        scrub_threshold (float): scrubbing threshold

    Inputs:
        ts_file (str): Path to file with timeseries
        fd_file (str): Path to file with framewise displacement values
        atlas_labels (Numpy Array): Array containing the labels in the atlas

    Outputs:
        out_file (str): Path to the quality check image

    Sinking:
    -   The quality check image

    """

    def connectivity_matrix(ts_file, fd_file, scrub_threshold):
        from sklearn.preprocessing import StandardScaler
        from nilearn.connectome import ConnectivityMeasure
        import numpy as np
        import pandas as pd
        import os

        timeseries = []
        perc_scrubbed = []

        ts = pd.read_csv(ts_file, sep='\t')
        regions = ts.columns.values
        ts = ts.values

        fd = pd.read_csv(fd_file).values.flatten()
        fd = np.hstack((0, fd))  # 0 for the first frame

        perc_scrubbed.append(1 - len(ts[fd < scrub_threshold]) / len(ts))

        ts = ts[fd <= scrub_threshold]
        ts = StandardScaler().fit_transform(ts)
        timeseries.append(ts)

        correlation_measure = ConnectivityMeasure(kind='partial correlation', vectorize=True, discard_diagonal=True)
        X = correlation_measure.fit_transform(timeseries)

        out_file = os.path.join(os.getcwd(), 'connectivity_matrix.csv')
        np.savetxt(out_file, X, delimiter=',')

        return X, out_file, timeseries, regions

    conn_matrix = Node(
        utility.Function(
            input_names=['ts_file', 'fd_file', 'scrub_threshold'],
            output_names=['X', 'out_file', 'timeseries', 'regions'],
            function=connectivity_matrix
        ),
        name='conn_matrix_wf'
    )

    wf.connect('inputspec', 'ts_file', conn_matrix, 'ts_file')
    wf.connect('inputspec', 'fd_file', conn_matrix, 'fd_file')
    conn_matrix.inputs.scrub_threshold = scrub_threshold

    qc_connectivity_matrix_wf = qc_connectivity_matrix('qc_connectivity_matrix_wf')
    wf.connect(conn_matrix, 'timeseries', qc_connectivity_matrix_wf, 'timeseries')
    wf.connect(conn_matrix, 'regions', qc_connectivity_matrix_wf, 'regions')
    wf.connect('inputspec', 'atlas_labels', qc_connectivity_matrix_wf, 'atlas_labels')

    wf.connect(conn_matrix, 'out_file', 'outputspec', 'out_file')
    wf.connect(conn_matrix, 'out_file', 'sinker', 'out_file')


@QcPipeline(inputspec_fields=['timeseries', 'atlas_labels', 'regions'],
            outputspec_fields=['out_file'])
def qc_connectivity_matrix(wf, **kwargs):
    """

    Create quality check images for the create_connectivity_matrix workflow

    Inputs:
        timeseries (DataFrame): timeseries DataFrame (output of create_connectivity_matrix-workflow)
        atlas_labels (Numpy Array): Array containing the labels in the atlas
        regions (Numpy Array): Array containing the regions

    Outputs:
        out_file (str): Path to the quality check image

    Sinking:
    -   The quality check image

    """

    def plot_connection_matrix(timeseries, atlas_labels, regions):
        from nilearn.connectome import ConnectivityMeasure
        from PUMI.PAINTeR import plot_matrix
        import numpy as np
        import os

        labels = regions
        l = atlas_labels
        modules = np.insert(l, 0, "GlobSig")

        correlation_measure = ConnectivityMeasure(kind='partial correlation', vectorize=True, discard_diagonal=True)
        _ = correlation_measure.fit_transform(timeseries)  # these are the features

        # double-check the mean matrix visually
        mat = correlation_measure.mean_
        # mat=mat[1:, 1:] #fisrt row and column is global signal
        mat[range(mat.shape[0]), range(mat.shape[0])] = 0  # zero diag

        filename = os.getcwd() + '/connection_matrix.png'
        plot_matrix(mat, labels, modules, filename)

        return filename

    plot_connection_matrix_wf = Node(
        utility.Function(
            input_names=['timeseries', 'atlas_labels', 'regions'],
            output_names=['out_file'],
            function=plot_connection_matrix),
        name='plot_connection_matrix_wf'
    )
    wf.connect('inputspec', 'timeseries', plot_connection_matrix_wf, 'timeseries')
    wf.connect('inputspec', 'atlas_labels', plot_connection_matrix_wf, 'atlas_labels')
    wf.connect('inputspec', 'regions', plot_connection_matrix_wf, 'regions')

    # sinking
    wf.connect(plot_connection_matrix_wf, 'out_file', 'sinker', 'qc_connectivity_matrix')

    # output
    wf.connect(plot_connection_matrix_wf, 'out_file', 'outputspec', 'out_file')
