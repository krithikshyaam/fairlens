"""
core/gemini.py
Calls Google Gemini API to generate plain-English explanations
of bias findings. Gracefully degrades if no API key is set.
"""

import os
from models.schemas import FairnessMetrics, FeatureImportance

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

_model = None


def _get_model():
    global _model
    if _model is not None:
        return _model

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or not GENAI_AVAILABLE:
        return None

    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel("gemini-1.5-flash")
    return _model


def explain_bias(
    dataset_name: str,
    target_column: str,
    protected_attribute: str,
    metrics: FairnessMetrics,
    feature_importances: list[FeatureImportance],
) -> str:
    """
    Generate a natural language explanation of bias findings.
    Falls back to a template explanation if Gemini is unavailable.
    """
    model = _get_model()
    if model is None:
        return _template_explanation(
            dataset_name, target_column, protected_attribute, metrics, feature_importances
        )

    top_features = ", ".join(
        f"{f.feature} (SHAP={f.shap_value:.4f})"
        for f in feature_importances[:5]
    )

    group_rates = "\n".join(
        f"  - {g}: {r:.1%} positive prediction rate"
        for g, r in metrics.group_positive_rates.items()
    )

    prompt = f"""You are a fairness auditor explaining AI bias findings to a non-technical stakeholder.

Dataset: {dataset_name}
Target variable: {target_column}
Protected attribute being audited: {protected_attribute}

Fairness metrics:
- Demographic Parity Difference: {metrics.demographic_parity_difference:.4f} (0 = perfect fairness)
- Equalized Odds Difference: {metrics.equalized_odds_difference:.4f} (0 = perfect fairness)
- Disparate Impact Ratio: {metrics.disparate_impact_ratio:.4f} (1.0 = perfect fairness, <0.8 = disparate impact)
- Overall model accuracy: {metrics.overall_accuracy:.1%}
- Bias severity: {metrics.bias_severity.upper()}

Group positive prediction rates:
{group_rates}

Top features driving predictions (by SHAP importance):
{top_features}

Write a clear, concise 3-4 sentence explanation of:
1. What bias was found and which groups are affected
2. How severe it is in practical terms
3. Which features are most responsible

Use plain English. No bullet points. No technical jargon. Write as if explaining to a hiring manager or loan officer who needs to understand the risk.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return _template_explanation(
            dataset_name, target_column, protected_attribute, metrics, feature_importances
        )


def explain_mitigation(
    protected_attribute: str,
    strategy: str,
    before: FairnessMetrics,
    after: FairnessMetrics,
) -> str:
    """Explain what the mitigation achieved in plain English."""
    model = _get_model()
    if model is None:
        return _template_mitigation(protected_attribute, strategy, before, after)

    dpd_change = before.demographic_parity_difference - after.demographic_parity_difference
    dir_change = after.disparate_impact_ratio - before.disparate_impact_ratio

    prompt = f"""You are a fairness auditor summarising the effect of bias mitigation.

Protected attribute: {protected_attribute}
Strategy applied: {strategy}

Before mitigation:
- Demographic Parity Difference: {before.demographic_parity_difference:.4f}
- Disparate Impact Ratio: {before.disparate_impact_ratio:.4f}
- Severity: {before.bias_severity}

After mitigation:
- Demographic Parity Difference: {after.demographic_parity_difference:.4f}
- Disparate Impact Ratio: {after.disparate_impact_ratio:.4f}
- Severity: {after.bias_severity}

Improvement:
- DPD reduced by {dpd_change:.4f}
- DIR improved by {dir_change:.4f}

Write 2-3 sentences summarising what the mitigation achieved. Be specific about improvement numbers. Plain English only.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return _template_mitigation(protected_attribute, strategy, before, after)


# ─── Fallback templates ────────────────────────────────────────────────────

def _template_explanation(
    dataset_name, target_column, protected_attribute, metrics, feature_importances
) -> str:
    severity_desc = {
        "low": "minimal bias — the model treats groups nearly equally",
        "medium": "moderate bias that may warrant attention before deployment",
        "high": "significant bias that creates materially different outcomes across groups",
    }
    top_feat = feature_importances[0].feature if feature_importances else "unknown"
    worst_group = min(metrics.group_positive_rates, key=metrics.group_positive_rates.get)
    best_group = max(metrics.group_positive_rates, key=metrics.group_positive_rates.get)

    return (
        f"The model shows {severity_desc.get(metrics.bias_severity, 'bias')} "
        f"with respect to '{protected_attribute}' in the '{dataset_name}' dataset. "
        f"The group '{worst_group}' receives positive '{target_column}' predictions "
        f"{metrics.group_positive_rates[worst_group]:.1%} of the time, compared to "
        f"{metrics.group_positive_rates[best_group]:.1%} for '{best_group}' — "
        f"a Demographic Parity gap of {metrics.demographic_parity_difference:.4f}. "
        f"The feature '{top_feat}' is the strongest driver of predictions and may be "
        f"acting as a proxy for the protected attribute."
    )


def _template_mitigation(protected_attribute, strategy, before, after) -> str:
    dpd_change = before.demographic_parity_difference - after.demographic_parity_difference
    return (
        f"Applying '{strategy}' mitigation on '{protected_attribute}' reduced the "
        f"Demographic Parity Difference from {before.demographic_parity_difference:.4f} "
        f"to {after.demographic_parity_difference:.4f} (improvement of {dpd_change:.4f}). "
        f"Bias severity changed from '{before.bias_severity}' to '{after.bias_severity}'."
    )
