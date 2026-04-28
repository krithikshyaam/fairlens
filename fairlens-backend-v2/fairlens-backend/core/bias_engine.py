"""
core/bias_engine.py
Computes comprehensive fairness metrics.

Metrics:
  - Demographic Parity Difference (DPD)
  - Equalized Odds Difference (EOD)
  - Disparate Impact Ratio (DIR)
  - Average Odds Difference (AOD)
  - Equal Opportunity Difference (EQOD)
  - Theil Index (entropy-based inequality)
  - Statistical Parity Ratio (SPR)
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from models.schemas import FairnessMetrics


def _bias_severity(dpd: float, dir_: float, theil: float) -> str:
    dpd_abs = abs(dpd)
    if dpd_abs < 0.1 and dir_ > 0.8 and theil < 0.1:
        return "low"
    elif dpd_abs < 0.2 and dir_ > 0.6:
        return "medium"
    else:
        return "high"


def train_model(X: pd.DataFrame, y: pd.Series):
    if len(X) > 50_000:
        model = LogisticRegression(max_iter=1000, random_state=42)
    else:
        model = GradientBoostingClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model


def compute_theil_index(group_positive_rates: dict) -> float:
    """Theil T index — entropy-based measure of inequality across groups."""
    rates = np.array(list(group_positive_rates.values()), dtype=float)
    rates = rates[rates > 0]
    if len(rates) < 2:
        return 0.0
    mean_rate = rates.mean()
    if mean_rate == 0:
        return 0.0
    ratios = rates / mean_rate
    theil = float(np.mean(ratios * np.log(ratios + 1e-10)))
    return round(max(0.0, theil), 4)


def compute_metrics(
    df_raw: pd.DataFrame,
    X: pd.DataFrame,
    y: pd.Series,
    model,
    protected_attribute: str,
    positive_label,
) -> FairnessMetrics:
    y_pred = model.predict(X)
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
        y_g  = y_true[mask]
        yp_g = y_pred_s[mask]

        group_positive_rates[g] = float((yp_g == pos).mean())
        group_accuracies[g]     = float((y_g == yp_g).mean())

        tp_mask = y_g == pos
        tn_mask = y_g != pos
        group_tpr[g] = float((yp_g[tp_mask] == pos).mean()) if tp_mask.sum() > 0 else 0.0
        group_fpr[g] = float((yp_g[tn_mask] == pos).mean()) if tn_mask.sum() > 0 else 0.0

    rates = list(group_positive_rates.values())
    tprs  = list(group_tpr.values())
    fprs  = list(group_fpr.values())

    # ── Core metrics ──────────────────────────────────────────────────────
    dpd = float(max(rates) - min(rates)) if len(rates) >= 2 else 0.0

    tpr_diff = float(max(tprs) - min(tprs)) if len(tprs) >= 2 else 0.0
    fpr_diff = float(max(fprs) - min(fprs)) if len(fprs) >= 2 else 0.0
    eod = float(max(tpr_diff, fpr_diff))

    dir_ = float(min(rates) / max(rates)) if len(rates) >= 2 and max(rates) > 0 else 1.0

    # ── Extended metrics ──────────────────────────────────────────────────
    # Average Odds Difference: avg of (TPR gap + FPR gap) / 2
    aod = round((tpr_diff + fpr_diff) / 2, 4)

    # Equal Opportunity Difference: difference in true positive rates
    eqod = round(max(tprs) - min(tprs), 4) if len(tprs) >= 2 else 0.0

    # Theil Index
    theil = compute_theil_index(group_positive_rates)

    # Statistical Parity Ratio (same as DIR but named explicitly)
    spr = round(dir_, 4)

    overall_acc = float(accuracy_score(y_true, y_pred_s))

    return FairnessMetrics(
        demographic_parity_difference=round(dpd, 4),
        equalized_odds_difference=round(eod, 4),
        disparate_impact_ratio=round(dir_, 4),
        overall_accuracy=round(overall_acc, 4),
        average_odds_difference=aod,
        equal_opportunity_difference=eqod,
        theil_index=theil,
        statistical_parity_ratio=spr,
        group_positive_rates={k: round(v, 4) for k, v in group_positive_rates.items()},
        group_accuracies={k: round(v, 4) for k, v in group_accuracies.items()},
        group_tpr={k: round(v, 4) for k, v in group_tpr.items()},
        group_fpr={k: round(v, 4) for k, v in group_fpr.items()},
        bias_severity=_bias_severity(dpd, dir_, theil),
    )


def run_bias_analysis(df_raw, X, y, protected_attribute, positive_label):
    model = train_model(X, y)
    metrics = compute_metrics(df_raw, X, y, model, protected_attribute, positive_label)
    return metrics, model
