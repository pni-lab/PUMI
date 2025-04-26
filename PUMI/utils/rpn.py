def rpn_model(file):

    from sklearn.feature_selection import SelectKBest
    from sklearn.linear_model import ElasticNet
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import RobustScaler
    from sklearn.feature_selection import f_regression
    import numpy as np
    import json

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
