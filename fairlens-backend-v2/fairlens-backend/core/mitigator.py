"""
core/mitigator.py
Implements three bias mitigation strategies:

  1. reweighing       - Pre-processing: reweight training samples so
                        protected groups have equal influence.
  2. threshold_optimizer - Post-processing: find per-group decision
                        thresholds that equalize a chosen metric.
  3. correlation_removal - Pre-processing: remove features highly
                        correlated with protected attributes.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from models.schemas import FairnessMetrics
from core.bias_engine import compute_metrics, train_model


# ─── Strategy 1: Reweighing ────────────────────────────────────────────────

def _compute_sample_weights(
    y: pd.Series,
    protected: pd.Series,
    positive_label: str,
) -> np.ndarray:
    """
    Compute instance weights that equalise the expected positive rate
    across each protected group (IBM Reweighing algorithm).
    """
    df = pd.DataFrame({"y": y.astype(str), "p": protected.astype(str)})
    n = len(df)
    weights = np.ones(n)

    pos = str(positive_label)

    for g in df["p"].unique():
        for outcome in [pos, "other"]:
            mask_g = df["p"] == g
            mask_o = df["y"] == pos if outcome == pos else df["y"] != pos
            combined = mask_g & mask_o

            if combined.sum() == 0:
                continue

            expected = (mask_g.sum() / n) * (mask_o.sum() / n)
            observed = combined.sum() / n

            w = expected / observed if observed > 0 else 1.0
            weights[combined.values] = w

    return weights


def apply_reweighing(
    df_raw: pd.DataFrame,
    X: pd.DataFrame,
    y: pd.Series,
    protected_attribute: str,
    positive_label,
) -> tuple[FairnessMetrics, object]:
    """Retrain with reweighed samples and return new metrics + model."""
    protected = df_raw.loc[X.index, protected_attribute].astype(str)
    weights = _compute_sample_weights(y.astype(str), protected, str(positive_label))

    if len(X) > 50_000:
        model = LogisticRegression(max_iter=1000, random_state=42)
    else:
        model = GradientBoostingClassifier(n_estimators=100, random_state=42)

    model.fit(X, y, sample_weight=weights)
    metrics = compute_metrics(df_raw, X, y, model, protected_attribute, positive_label)
    return metrics, model


# ─── Strategy 2: Threshold Optimizer ──────────────────────────────────────

def apply_threshold_optimizer(
    df_raw: pd.DataFrame,
    X: pd.DataFrame,
    y: pd.Series,
    model,
    protected_attribute: str,
    positive_label,
) -> tuple[FairnessMetrics, dict[str, float]]:
    """
    Post-processing: find per-group decision thresholds that minimise
    demographic parity difference while maintaining accuracy.
    Returns new metrics and the optimal thresholds per group.
    """
    protected = df_raw.loc[X.index, protected_attribute].astype(str)
    y_str = y.astype(str)
    pos = str(positive_label)

    # Get probability predictions
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        classes = list(model.classes_)
        # Try to match positive_label to classes (handles int, float, str)
        pos_label_cast = positive_label
        for cls in classes:
            try:
                if str(cls) == str(positive_label):
                    pos_label_cast = cls
                    break
            except Exception:
                pass
        pos_idx = classes.index(pos_label_cast) if pos_label_cast in classes else 0
        y_proba = proba[:, pos_idx]
    else:
        # No probabilities — return original metrics unchanged
        metrics = compute_metrics(df_raw, X, y, model, protected_attribute, positive_label)
        return metrics, {}

    groups = protected.unique()
    best_thresholds: dict[str, float] = {}

    # Find threshold per group that brings positive rate closest to global rate
    global_pos_rate = float((y_str == pos).mean())

    for g in groups:
        mask = (protected == g).values
        proba_g = y_proba[mask]
        best_t, best_diff = 0.5, float("inf")

        for t in np.linspace(0.1, 0.9, 17):
            pred_pos_rate = float((proba_g >= t).mean())
            diff = abs(pred_pos_rate - global_pos_rate)
            if diff < best_diff:
                best_diff, best_t = diff, t

        best_thresholds[g] = best_t

    # Apply per-group thresholds
    y_pred_opt = np.zeros(len(X), dtype=object)
    for g, t in best_thresholds.items():
        mask = (protected == g).values
        y_pred_opt[mask] = np.where(y_proba[mask] >= t, pos, "0")

    # Build a mock model wrapper so compute_metrics works
    class ThresholdModel:
        def predict(self, _X):
            return y_pred_opt

    metrics = compute_metrics(df_raw, X, y, ThresholdModel(), protected_attribute, positive_label)
    return metrics, {g: round(t, 3) for g, t in best_thresholds.items()}


# ─── Strategy 3: Correlation Removal ──────────────────────────────────────

def apply_correlation_removal(
    df_raw: pd.DataFrame,
    X: pd.DataFrame,
    y: pd.Series,
    protected_attribute: str,
    positive_label,
    correlation_threshold: float = 0.15,
) -> tuple[FairnessMetrics, object, list[str]]:
    """
    Pre-processing: drop features whose absolute Pearson correlation
    with the protected attribute exceeds the threshold, then retrain.
    Returns new metrics, model, and list of dropped features.
    """
    # Encoded protected attr (already numeric in X if encoded)
    if protected_attribute in X.columns:
        prot_series = X[protected_attribute]
    else:
        prot_series = df_raw.loc[X.index, protected_attribute].astype("category").cat.codes

    corrs = X.corrwith(prot_series).abs()
    drop_cols = corrs[corrs > correlation_threshold].index.tolist()

    # Never drop the protected attribute itself from X (it shouldn't be there)
    X_clean = X.drop(columns=[c for c in drop_cols if c in X.columns], errors="ignore")

    model = train_model(X_clean, y)
    metrics = compute_metrics(df_raw, X_clean, y, model, protected_attribute, positive_label)
    return metrics, model, drop_cols


# ─── Dispatch ──────────────────────────────────────────────────────────────

def run_mitigation(
    strategy: str,
    df_raw: pd.DataFrame,
    X: pd.DataFrame,
    y: pd.Series,
    model,
    protected_attribute: str,
    positive_label,
) -> tuple[FairnessMetrics, dict]:
    """
    Dispatch to the correct mitigation strategy.
    Returns (after_metrics, extra_info_dict).
    """
    if strategy == "reweighing":
        metrics, _ = apply_reweighing(df_raw, X, y, protected_attribute, positive_label)
        return metrics, {"strategy": "reweighing"}

    elif strategy == "threshold_optimizer":
        metrics, thresholds = apply_threshold_optimizer(
            df_raw, X, y, model, protected_attribute, positive_label
        )
        return metrics, {"strategy": "threshold_optimizer", "thresholds": thresholds}

    elif strategy == "correlation_removal":
        metrics, _, dropped = apply_correlation_removal(
            df_raw, X, y, protected_attribute, positive_label
        )
        return metrics, {"strategy": "correlation_removal", "dropped_features": dropped}

    else:
        raise ValueError(f"Unknown strategy: {strategy}. Choose from: reweighing, threshold_optimizer, correlation_removal")
