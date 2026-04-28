"""
core/bias_engine.py
Computes fairness metrics across protected attribute groups.

Metrics computed:
  - Demographic Parity Difference (DPD)
  - Equalized Odds Difference (EOD)
  - Disparate Impact Ratio (DIR)
  - Per-group positive rates and accuracy
  - Bias severity level
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import label_binarize
from models.schemas import FairnessMetrics


def _bias_severity(dpd: float, dir_: float) -> str:
    """Classify bias severity from key metrics."""
    dpd_abs = abs(dpd)
    if dpd_abs < 0.1 and dir_ > 0.8:
        return "low"
    elif dpd_abs < 0.2 and dir_ > 0.6:
        return "medium"
    else:
        return "high"


def train_model(X: pd.DataFrame, y: pd.Series):
    """Train a fast GradientBoosting classifier. Falls back to LR if too slow."""
    if len(X) > 50_000:
        model = LogisticRegression(max_iter=1000, random_state=42)
    else:
        model = GradientBoostingClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model


def compute_metrics(
    df_raw: pd.DataFrame,
    X: pd.DataFrame,
    y: pd.Series,
    model,
    protected_attribute: str,
    positive_label,
) -> FairnessMetrics:
    """
    Compute fairness metrics for a single protected attribute.

    Args:
        df_raw              - original (pre-encoded) dataframe
        X                   - encoded feature matrix (same index as df_raw after dropna)
        y                   - target series
        model               - fitted sklearn model
        protected_attribute - column name of the protected attribute
        positive_label      - the value considered "positive" outcome
    """
    y_pred = model.predict(X)

    # Align protected attribute with X index
    protected = df_raw.loc[X.index, protected_attribute].astype(str)
    y_true = y.astype(str)
    y_pred_s = pd.Series(y_pred.astype(str), index=X.index)
    pos = str(positive_label)

    groups = protected.unique().tolist()

    group_positive_rates: dict[str, float] = {}
    group_accuracies: dict[str, float] = {}
    group_tpr: dict[str, float] = {}
    group_fpr: dict[str, float] = {}

    for g in groups:
        mask = protected == g
        if mask.sum() == 0:
            continue

        y_g = y_true[mask]
        yp_g = y_pred_s[mask]

        # Positive prediction rate
        group_positive_rates[g] = float((yp_g == pos).mean())

        # Accuracy
        group_accuracies[g] = float((y_g == yp_g).mean())

        # True positive rate (sensitivity) — for equalized odds
        tp_mask = y_g == pos
        if tp_mask.sum() > 0:
            group_tpr[g] = float((yp_g[tp_mask] == pos).mean())
        else:
            group_tpr[g] = 0.0

        # False positive rate
        tn_mask = y_g != pos
        if tn_mask.sum() > 0:
            group_fpr[g] = float((yp_g[tn_mask] == pos).mean())
        else:
            group_fpr[g] = 0.0

    # ── Demographic Parity Difference ──────────────────────────────────
    # Largest positive rate gap across all group pairs
    rates = list(group_positive_rates.values())
    if len(rates) >= 2:
        dpd = float(max(rates) - min(rates))
    else:
        dpd = 0.0

    # ── Equalized Odds Difference ──────────────────────────────────────
    tprs = list(group_tpr.values())
    fprs = list(group_fpr.values())
    tpr_diff = float(max(tprs) - min(tprs)) if len(tprs) >= 2 else 0.0
    fpr_diff = float(max(fprs) - min(fprs)) if len(fprs) >= 2 else 0.0
    eod = float(max(tpr_diff, fpr_diff))

    # ── Disparate Impact Ratio ─────────────────────────────────────────
    # min_rate / max_rate  (1.0 = perfect parity, <0.8 = disparate impact)
    if len(rates) >= 2 and max(rates) > 0:
        dir_ = float(min(rates) / max(rates))
    else:
        dir_ = 1.0

    overall_acc = float(accuracy_score(y_true, y_pred_s))

    return FairnessMetrics(
        demographic_parity_difference=round(dpd, 4),
        equalized_odds_difference=round(eod, 4),
        disparate_impact_ratio=round(dir_, 4),
        overall_accuracy=round(overall_acc, 4),
        group_positive_rates={k: round(v, 4) for k, v in group_positive_rates.items()},
        group_accuracies={k: round(v, 4) for k, v in group_accuracies.items()},
        bias_severity=_bias_severity(dpd, dir_),
    )


def run_bias_analysis(
    df_raw: pd.DataFrame,
    X: pd.DataFrame,
    y: pd.Series,
    protected_attribute: str,
    positive_label,
) -> tuple[FairnessMetrics, object]:
    """
    Full pipeline: train model → compute metrics.
    Returns (metrics, model) so the model can be reused for SHAP.
    """
    model = train_model(X, y)
    metrics = compute_metrics(df_raw, X, y, model, protected_attribute, positive_label)
    return metrics, model
