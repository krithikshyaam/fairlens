"""
routers/mitigate.py
POST /mitigate
Applies a mitigation strategy to a previously analysed dataset.
"""

from fastapi import APIRouter, HTTPException
from core import store
from core.mitigator import run_mitigation
from core.gemini import explain_mitigation
from models.schemas import MitigateRequest, MitigationResult

router = APIRouter(prefix="/mitigate", tags=["Mitigation"])

VALID_STRATEGIES = {"reweighing", "threshold_optimizer", "correlation_removal"}


@router.post("", response_model=MitigationResult)
async def mitigate(req: MitigateRequest):
    """
    Apply a bias mitigation strategy to a previously analysed dataset.

    Strategies:
      - reweighing          : Pre-processing. Reweights training samples so
                              protected groups have equal influence on the model.
      - threshold_optimizer : Post-processing. Finds per-group decision thresholds
                              that equalise positive prediction rates.
      - correlation_removal : Pre-processing. Removes features highly correlated
                              with protected attributes, then retrains.

    Requires a valid analysis_id from a prior /analyze call.
    """
    if req.strategy not in VALID_STRATEGIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid strategy '{req.strategy}'. Choose from: {sorted(VALID_STRATEGIES)}"
        )

    # Load prior analysis
    saved = store.load(req.analysis_id)
    if saved is None:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis '{req.analysis_id}' not found. Run /analyze first."
        )

    df_raw = saved["df_raw"]
    X      = saved["X"]
    y      = saved["y"]
    model  = saved["model"]
    before_result = saved["result"]
    before_metrics = before_result.metrics

    # Parse positive label
    try:
        target_dtype = str(df_raw[req.target_column].dtype)
        if "int" in target_dtype:
            pos_label = int(req.positive_label)
        elif "float" in target_dtype:
            pos_label = float(req.positive_label)
        else:
            pos_label = req.positive_label
    except (ValueError, TypeError):
        pos_label = req.positive_label

    primary_attr = req.protected_attributes[0]

    # Run mitigation
    try:
        after_metrics, extra = run_mitigation(
            strategy=req.strategy,
            df_raw=df_raw,
            X=X,
            y=y,
            model=model,
            protected_attribute=primary_attr,
            positive_label=pos_label,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mitigation error: {str(e)}")

    # Compute improvement summary
    improvement = {
        "demographic_parity_difference": round(
            before_metrics.demographic_parity_difference - after_metrics.demographic_parity_difference, 4
        ),
        "equalized_odds_difference": round(
            before_metrics.equalized_odds_difference - after_metrics.equalized_odds_difference, 4
        ),
        "disparate_impact_ratio": round(
            after_metrics.disparate_impact_ratio - before_metrics.disparate_impact_ratio, 4
        ),
        "accuracy_delta": round(
            after_metrics.overall_accuracy - before_metrics.overall_accuracy, 4
        ),
    }

    # Gemini explanation
    try:
        gemini_text = explain_mitigation(
            protected_attribute=primary_attr,
            strategy=req.strategy,
            before=before_metrics,
            after=after_metrics,
        )
    except Exception:
        gemini_text = None

    mit_result = MitigationResult(
        analysis_id=req.analysis_id,
        strategy=req.strategy,
        before_metrics=before_metrics,
        after_metrics=after_metrics,
        improvement_summary=improvement,
        gemini_explanation=gemini_text,
    )

    # Update store with mitigation result for /report
    store.save(
        req.analysis_id,
        **saved,
        mitigation=mit_result,
    )

    return mit_result
