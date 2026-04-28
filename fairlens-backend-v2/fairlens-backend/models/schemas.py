from pydantic import BaseModel
from typing import Optional


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
    average_odds_difference: float = 0.0
    equal_opportunity_difference: float = 0.0
    theil_index: float = 0.0
    statistical_parity_ratio: float = 0.0
    group_positive_rates: dict
    group_accuracies: dict
    group_tpr: dict = {}
    group_fpr: dict = {}
    bias_severity: str


class FeatureImportance(BaseModel):
    feature: str
    shap_value: float
    direction: str


class DataProfile(BaseModel):
    row_count: int
    column_count: int
    columns: list[ColumnProfile]
    class_balance: dict
    protected_attributes: list[str]
    target_column: str


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


class MitigateRequest(BaseModel):
    analysis_id: str
    strategy: str
    target_column: str
    protected_attributes: list[str]
    positive_label: Optional[str | int | float] = 1


class MitigationResult(BaseModel):
    analysis_id: str
    strategy: str
    before_metrics: FairnessMetrics
    after_metrics: FairnessMetrics
    improvement_summary: dict
    gemini_explanation: Optional[str] = None


class ReportRequest(BaseModel):
    analysis_id: str
    include_mitigation: bool = False
