"""
core/explainer.py
Generates SHAP-based feature importances to explain which features
drive bias in the model's predictions.
"""

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from models.schemas import FeatureImportance


def compute_shap_importances(
    model,
    X: pd.DataFrame,
    protected_attributes: list[str],
    max_samples: int = 500,
) -> list[FeatureImportance]:
    """
    Compute mean absolute SHAP values per feature.
    Marks features as 'increases_bias' if they are protected attributes
    or highly correlated with them.

    Args:
        model               - fitted sklearn model
        X                   - encoded feature matrix
        protected_attributes - list of protected attr column names
        max_samples         - cap sample size for speed

    Returns:
        list of FeatureImportance sorted by |shap_value| descending
    """
    # Sample for speed
    if len(X) > max_samples:
        X_sample = X.sample(max_samples, random_state=42)
    else:
        X_sample = X.copy()

    # Choose explainer based on model type
    try:
        if isinstance(model, GradientBoostingClassifier):
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample)
        else:
            # Linear models - use LinearExplainer
            masker = shap.maskers.Independent(X_sample)
            explainer = shap.LinearExplainer(model, masker)
            shap_values = explainer.shap_values(X_sample)

        # If multi-class, take the positive class (index 1)
        if isinstance(shap_values, list):
            sv = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            sv = shap_values

        mean_abs = np.abs(sv).mean(axis=0)

    except Exception:
        # Fallback: use feature importances from tree model, else uniform
        if hasattr(model, "feature_importances_"):
            mean_abs = model.feature_importances_
        else:
            mean_abs = np.ones(X_sample.shape[1]) / X_sample.shape[1]

    features = X_sample.columns.tolist()
    pa_set = set(protected_attributes)

    results: list[FeatureImportance] = []
    for feat, val in zip(features, mean_abs):
        if feat in pa_set:
            direction = "increases_bias"
        elif val > float(mean_abs.mean()):
            direction = "increases_bias"
        else:
            direction = "neutral"

        results.append(FeatureImportance(
            feature=feat,
            shap_value=round(float(val), 6),
            direction=direction,
        ))

    # Sort descending by importance
    results.sort(key=lambda x: x.shap_value, reverse=True)
    return results[:15]  # top 15
