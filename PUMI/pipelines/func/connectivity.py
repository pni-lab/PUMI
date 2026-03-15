import traits
from nipype.interfaces import utility
from PUMI.engine import FuncPipeline, NestedNode as Node


@FuncPipeline(inputspec_fields=['ts_files', 'fd_files', 'scrub_threshold'],
              outputspec_fields=['features', 'out_file'])
def calculate_connectivity(wf, **kwargs):

    def calc_connectivity(ts_files, fd_files, scrub_threshold):
        import os
        import pandas as pd
        import numpy as np
        from PUMI.PAINTeR import load_timeseries, connectivity_matrix

        if not isinstance(ts_files, (list, np.ndarray)):  # in this case we assume we have a string or path-like object
            ts_files = [ts_files]
        if not isinstance(fd_files, (list, np.ndarray)):  # in this case we assume we have a string or path-like object
            fd_files = [fd_files]
        FD = []
        mean_FD = []
        median_FD = []
        max_FD = []
        perc_scrubbed = []
        for f in fd_files:
            fd = pd.read_csv(f, sep="\t").values.flatten()
            fd = np.insert(fd, 0, 0)
            FD.append(fd.ravel())
            mean_FD.append(fd.mean())
            median_FD.append(np.median(fd))
            max_FD.append(fd.max())
            perc_scrubbed.append(100 - 100 * len(fd) / len(fd[fd <= scrub_threshold]))

        df = pd.DataFrame()
        df['ts_file'] = ts_files
        df['fd_file'] = fd_files
        df['meanFD'] = mean_FD
        df['medianFD'] = median_FD
        df['maxFD'] = max_FD
        df['perc_scrubbed'] = perc_scrubbed

        ts, labels = load_timeseries(ts_files, df, scrubbing=True, scrub_threshold=scrub_threshold)
        features, cm = connectivity_matrix(np.array(ts))

        path = os.path.abspath('motion.csv')
        df.to_csv(path)
        return features, path

    connectivity_wf = Node(
        utility.Function(
            input_names=['ts_files', 'fd_files', 'scrub_threshold'],
            output_names=['features', 'out_file'],
            function=calc_connectivity
        ),
        name="connectivity_wf"
    )
    wf.connect('inputspec', 'ts_files', connectivity_wf, 'ts_files')
    wf.connect('inputspec', 'fd_files', connectivity_wf, 'fd_files')

    if isinstance(wf.get_node('inputspec').inputs.scrub_threshold, traits.trait_base._Undefined):
        connectivity_wf.inputs.scrub_threshold = .15
    else:
        wf.connect('inputspec', 'scrub_threshold', connectivity_wf, 'scrub_threshold')

    wf.connect(connectivity_wf, 'features', 'outputspec', 'features')
    wf.connect(connectivity_wf, 'out_file', 'outputspec', 'out_file')

    wf.connect(connectivity_wf, 'out_file', 'sinker', 'connectivity')
