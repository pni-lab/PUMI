#!/usr/bin/env python3

"""
Pain prediction related pipeline decorators.
"""

from PUMI.engine import FuncPipeline, NestedNode as Node
from nipype.interfaces import utility
import traits

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


@FuncPipeline(inputspec_fields=['X', 'in_file'],
              outputspec_fields=['score', 'out_file'])
def predict_pain_sensitivity_rpn(wf, **kwargs):
    """

    Perform pain sensitivity prediction using the RPN signature
    (Resting-state Pain susceptibility Network signature).
    Further information regarding the signature: https://spisakt.github.io/RPN-signature/

    Inputs:
        X (array-like): Input data for pain sensitivity prediction
        in_file (str): Path to the bold file that was used to create X

    Outputs:
        predicted (float): Predicted pain sensitivity score
        out_file (str): Absolute path to the output CSV file containing the prediction result

    Sinking:
        CSV file containing the prediction result

    """

    def predict(X, in_file):
        from PUMI.utils import rpn_model
        import pandas as pd
        import PUMI
        import os
        import importlib

        with importlib.resources.path('resources', 'model_rpn.json') as file:
            model_json = file

        model = rpn_model(file=model_json)
        predicted = model.predict(X)

        path = os.path.abspath('rpn-prediction.csv')
        df = pd.DataFrame()
        df['in_file'] = [in_file]
        df['RPN'] = predicted
        df.to_csv(path, index=False)
        return predicted, path

    predict_wf = Node(
        utility.Function(
            input_names=['X', 'in_file'],
            output_names=['score', 'out_file'],
            function=predict
        ),
        name="predict_wf"
    )
    wf.connect('inputspec', 'X', predict_wf, 'X')
    wf.connect('inputspec', 'in_file', predict_wf, 'in_file')

    wf.connect(predict_wf, 'score', 'outputspec', 'score')
    wf.connect(predict_wf, 'out_file', 'outputspec', 'out_file')
    wf.connect(predict_wf, 'out_file', 'sinker', 'rpn')


@FuncPipeline(inputspec_fields=['X', 'in_file'],
              outputspec_fields=['score', 'out_file'])
def predict_pain_sensitivity_rcpl(wf, model_path=None, **kwargs):
    """

    Perform pain sensitivity prediction using RCPL signature
    (Resting-state functional Connectivity signature of Pain-related Learning).
    Further information regarding the signature: https://github.com/kincsesbalint/paintone_rsn

    Parameters:
        model_path (str, optional): Path to the pre-trained model relative to PUMI's data_in folder.
                                    If set to None, PUMI's build in RCPL model is used.

    Inputs:
        X (array-like): Input data for pain sensitivity prediction
        in_file (str): Path to the bold file that was used to create X

    Outputs:
        predicted (float): Predicted pain sensitivity score
        out_file (str): Absolute path to the output CSV file containing the prediction result

    Sinking:
        CSV file containing the prediction result

    """

    def predict(X, in_file, model_path):
        import pandas as pd
        import os
        import PUMI
        import joblib
        import importlib

        if model_path is None:
            with importlib.resources.path('resources', 'rcpl_model.sav') as file:
                model = joblib.load(file)
        else:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")

            data_in_folder = os.path.join(os.path.dirname(os.path.abspath(PUMI.__file__)), '..', 'data_in')
            model_path = os.path.join(data_in_folder, model_path)
            model = joblib.load(model_path)

        predicted = model.predict(X)

        path = os.path.abspath('rcpl-prediction.csv')
        df = pd.DataFrame()
        df['in_file'] = [in_file]
        df['RCPL'] = predicted
        df.to_csv(path, index=False)

        return predicted, path

    predict_wf = Node(
        utility.Function(
            input_names=['X', 'in_file', 'model_path'],
            output_names=['score', 'out_file'],
            function=predict
        ),
        name="predict_wf"
    )
    wf.connect('inputspec', 'X', predict_wf, 'X')
    wf.connect('inputspec', 'in_file', predict_wf, 'in_file')
    predict_wf.inputs.model_path = model_path

    wf.connect(predict_wf, 'score', 'outputspec', 'score')
    wf.connect(predict_wf, 'out_file', 'outputspec', 'out_file')
    wf.connect(predict_wf, 'out_file', 'sinker', 'rcpl')


@FuncPipeline(inputspec_fields=['rpn_out_file', 'rcpl_out_file'],
              outputspec_fields=['out_file'])
def collect_pain_predictions(wf, **kwargs):
    """

    Merge the out_file's of pain sensitivity predictions generated using the RCPL and RPN methods into one file

    Inputs:
        rpn_out_file (str): Path to the out_file generated by the RPN method
        rcpl_out_file (str): Path to the out_file generated by the RCPL method

    Outputs:
        out_file (str): Absolute path to the output CSV file containing the RPN and RCPL predictions.

    Sinking:
        CSV file containing RPN and RCPL predictions

   """

    def merge_predictions(rpn_out_file, rcpl_out_file):
        import pandas as pd
        import os

        df_rpn = pd.read_csv(rpn_out_file)
        df_rcpl = pd.read_csv(rcpl_out_file)

        # Check if in_file columns are the same
        if df_rpn['in_file'].iloc[0] != df_rcpl['in_file'].iloc[0]:
            raise ValueError("The 'in_file' columns in the two CSV files are not the same!")

        merged_df = pd.DataFrame()
        merged_df['in_file'] = df_rpn['in_file']
        merged_df['RPN'] = df_rpn['RPN']
        merged_df['RCPL'] = df_rcpl['RCPL']

        path = os.path.abspath('pain-sensitivity-predictions.csv')
        merged_df.to_csv(path, index=False)

        return path

    merge_predictions_wf = Node(
        utility.Function(
            input_names=['rpn_out_file', 'rcpl_out_file'],
            output_names=['out_file'],
            function=merge_predictions
        ),
        name="merge_predictions_wf"
    )
    wf.connect('inputspec', 'rpn_out_file', merge_predictions_wf, 'rpn_out_file')
    wf.connect('inputspec', 'rcpl_out_file', merge_predictions_wf, 'rcpl_out_file')

    wf.connect(merge_predictions_wf, 'out_file', 'outputspec', 'out_file')
    wf.connect(merge_predictions_wf, 'out_file', 'sinker', 'pain_predictions')