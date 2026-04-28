from pydantic import BaseModel
from typing import Optional


# ──────────────────────────────────────────────
# Shared sub-models
# ──────────────────────────────────────────────

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_rate: float
    unique_count: int
    is_protected: bool
    sample_values: list


class FairnessMetrics(BaseModel):
    demographic_parity_difference: float
    equalized_odds_difference: float
    disparate_impact_ratio: float
    overall_accuracy: float
    group_positive_rates: dict        # {group_value: positive_rate}
    group_accuracies: dict            # {group_value: accuracy}
    bias_severity: str                # "low" | "medium" | "high"


class FeatureImportance(BaseModel):
    feature: str
    shap_value: float                 # mean absolute SHAP value
    direction: str                    # "increases_bias" | "reduces_bias" | "neutral"


class DataProfile(BaseModel):
    row_count: int
    column_count: int
    columns: list[ColumnProfile]
    class_balance: dict               # {label: count}
    protected_attributes: list[str]
    target_column: str


# ──────────────────────────────────────────────
# /analyze  request / response
# ──────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    target_column: str
    protected_attributes: list[str]
    positive_label: Optional[str | int | float] = 1


class AnalysisResult(BaseModel):
    model_config = {"protected_namespaces": ()}
    analysis_id: str
    dataset_name: str
    target_column: str
    protected_attributes: list[str]
    data_profile: DataProfile
    metrics: FairnessMetrics
    feature_importances: list[FeatureImportance]
    gemini_explanation: Optional[str] = None
    model_type: str


# ──────────────────────────────────────────────
# /mitigate  request / response
# ──────────────────────────────────────────────

class MitigateRequest(BaseModel):
    analysis_id: str
    strategy: str                     # "reweighing" | "threshold_optimizer" | "adversarial"
    target_column: str
    protected_attributes: list[str]
    positive_label: Optional[str | int | float] = 1


class MitigationResult(BaseModel):
    analysis_id: str
    strategy: str
    before_metrics: FairnessMetrics
    after_metrics: FairnessMetrics
    improvement_summary: dict         # metric_name -> delta
    gemini_explanation: Optional[str] = None


# ──────────────────────────────────────────────
# /report  request
# ──────────────────────────────────────────────

class ReportRequest(BaseModel):
    analysis_id: str
    include_mitigation: bool = False
