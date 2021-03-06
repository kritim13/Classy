import pandas as pd
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from catboost import CatBoostClassifier, Pool
from catboost.utils import get_confusion_matrix
from common import create_logger
from datasets import single_label_multiclass_annotated_study_design

logger = create_logger()
# https://github.com/catboost/tutorials/blob/2c16945f850503bfaa631176e87588bc5ce0ca1c/text_features/text_features_in_catboost.ipynb


# def train_validate_catboost_model(train_data, test_data, train_features, target_feature, text_features, params, verbose=True):
#     X_train = train_data[train_features]
#     y_train = train_data[target_feature]
#     X_test = test_data[train_features]
#     y_test = test_data[target_feature]
#
#     train_pool = Pool(
#         X_train,
#         y_train,
#         feature_names=list(train_features),
#         text_features=text_features)
#     test_pool = Pool(
#         X_test,
#         y_test,
#         feature_names=list(train_features),
#         text_features=text_features)
#
#     catboost_default_params = {
#         'iterations': 1000,
#         'learning_rate': 0.03,
#         'eval_metric': 'Accuracy',
#         'task_type': 'GPU'
#     }
#     params = {**catboost_default_params, **params}
#     model = CatBoostClassifier(**params)
#     model.fit(train_pool, eval_set=test_pool, verbose=verbose)
#     prediction = model.predict(test_pool)
#     acc = accuracy_score(y_test, prediction)
#     f1 = f1_score(y_test, prediction, average=None)
#     f1_macro = f1_score(y_test, prediction, average="macro")
#     logger.info(f"accuracy: {acc}")
#     logger.info(f"f1: {f1}")
#     logger.info(f"f1_macro: {f1_macro}")
#     return model, acc, f1, f1_macro, params

def train_validate_catboost_model(train_data, test_data, train_features, target_feature, text_features, params, verbose=True, logging=True):
    X_train = train_data[train_features]
    y_train = train_data[target_feature]
    catboost_default_params = {
        'iterations': 1000,
        'learning_rate': 0.03,
        'eval_metric': 'Accuracy',
        'task_type': 'GPU'
    }
    params = {**catboost_default_params, **params}
    model = CatBoostClassifier(**params)

    train_pool = Pool(
        X_train,
        y_train,
        feature_names=list(train_features),
        text_features=text_features)

    if test_data is not None:
        X_test = test_data[train_features]
        y_test = test_data[target_feature]

        test_pool = Pool(
            X_test,
            y_test,
            feature_names=list(train_features),
            text_features=text_features)
        model.fit(train_pool, eval_set=test_pool, verbose=verbose)

        prediction = model.predict(test_pool)
        acc = accuracy_score(y_test, prediction)
        f1 = f1_score(y_test, prediction, average=None)
        f1_macro = f1_score(y_test, prediction, average="macro")
        confusion_matrix = get_confusion_matrix(model, test_pool)
        if logging:
            logger.info(f"accuracy: {acc}")
            logger.info(f"f1: {f1}")
            logger.info(f"f1_macro: {f1_macro}")
        return model, acc, f1, f1_macro, confusion_matrix, params

    else:
        model.fit(train_pool, verbose=verbose)
        return model

if __name__=="__main__":
    data_dir = Path('/media/wwymak/Storage/coronawhy/nlp_datasets')
    annotations_filepath = (data_dir / 'cord19_study_design_labelled' / 'design.csv')
    metadata_filepath = (data_dir/'metadata.csv.zip')
    design_labelled_metadata = single_label_multiclass_annotated_study_design(annotations_filepath, metadata_filepath)
    logger.info(f"design metadata shape: {design_labelled_metadata.shape}")
    # shuffle dataset
    design_labelled_metadata = design_labelled_metadata[['abstract', 'title', 'label']].sample(frac=1.0)
    test_set_len = len(design_labelled_metadata) //5
    results = []
    params = {}
    for i in range(5):
        test = design_labelled_metadata.iloc[i * test_set_len : (i+1)* test_set_len]
        train = design_labelled_metadata[~design_labelled_metadata.index.isin(test.index)]
        model, acc, f1, f1_macro,confusion_matrix, params = train_validate_catboost_model(
            train, test,
            ['abstract', 'title'],
            'label',
            text_features=['abstract', 'title'], params={})
        results.append({
            "i": i,
            "f1": f1,
            "acc": acc,
            'f1_macro': f1_macro,
            'confusion_matrix': confusion_matrix
        })

    results = pd.DataFrame(results)
    params_str = ",".join([f"{k}={v}" for k, v in params.items()])
    results.to_csv(f'catboost_text_Features_{params_str}.csv', index=False)
    print(pd.DataFrame(results))
    # train = design_labelled_metadata[['abstract', 'title', 'label']].sample(frac=0.8)
    # test = design_labelled_metadata[~design_labelled_metadata.index.isin(train.index)]
    # X_train = train[['abstract', 'title']]
    # y_train = train.label
    # X_test = test[['abstract', 'title']]
    # y_test = test.label
    #
    # train_pool = Pool(
    #     X_train,
    #     y_train, feature_names=list(X_train),
    #     text_features=['abstract', 'title'] )
    # test_pool = Pool(
    #     X_test,
    #     y_test, feature_names = list(X_test),
    #     text_features=['abstract', 'title'])
    #
    # catboost_default_params = {
    #     'iterations': 1000,
    #     'learning_rate': 0.03,
    #     'eval_metric': 'Accuracy',
    #     'task_type': 'GPU'
    # }
    #
    #
    # model = CatBoostClassifier(**catboost_default_params)
    # model.fit(train_pool, eval_set=test_pool, verbose=True)

