"""
routers/analyze.py
POST /analyze
Accepts a dataset file + config, runs the full bias analysis pipeline.
"""

import uuid
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import json

from core.profiler import load_dataframe, profile_dataframe
from core.encoder import encode_dataframe
from core.bias_engine import run_bias_analysis
from core.explainer import compute_shap_importances
from core.gemini import explain_bias
from core import store
from models.schemas import AnalysisResult

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("", response_model=AnalysisResult)
async def analyze(
    file: UploadFile = File(..., description="Dataset file (CSV, JSON, or Parquet)"),
    target_column: str = Form(..., description="Name of the target/label column"),
    protected_attributes: str = Form(
        ...,
        description='JSON array of protected attribute column names, e.g. ["race","gender"]'
    ),
    positive_label: str = Form(
        "1",
        description="The value that represents a positive outcome in the target column"
    ),
):
    """
    Run the full FairLens bias analysis pipeline on an uploaded dataset.

    Steps:
      1. Load dataset
      2. Profile data
      3. Encode features
      4. Train model + compute fairness metrics
      5. Compute SHAP feature importances
      6. Generate Gemini explanation
      7. Return full AnalysisResult
    """
    # Parse protected attributes
    try:
        protected_list: list[str] = json.loads(protected_attributes)
        if not isinstance(protected_list, list):
            raise ValueError
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(
            status_code=422,
            detail="protected_attributes must be a valid JSON array, e.g. [\"race\",\"gender\"]"
        )

    # Load file
    try:
        file_bytes = await file.read()
        df_raw = load_dataframe(file_bytes, file.filename or "upload.csv")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load dataset: {str(e)}")

    # Validate columns exist
    missing = [c for c in protected_list + [target_column] if c not in df_raw.columns]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Columns not found in dataset: {missing}. Available: {list(df_raw.columns)}"
        )

    if len(df_raw) < 50:
        raise HTTPException(status_code=422, detail="Dataset must have at least 50 rows.")

    # Parse positive label to match data type
    try:
        target_dtype = str(df_raw[target_column].dtype)
        if "int" in target_dtype:
            pos_label = int(positive_label)
        elif "float" in target_dtype:
            pos_label = float(positive_label)
        else:
            pos_label = positive_label
    except ValueError:
        pos_label = positive_label

    # Profile
    data_profile = profile_dataframe(df_raw, target_column, protected_list)

    # Encode
    try:
        X, y, encoders = encode_dataframe(df_raw, target_column, protected_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encoding error: {str(e)}")

    # Use first protected attribute for primary metric computation
    primary_attr = protected_list[0]

    # Bias analysis
    try:
        metrics, model = run_bias_analysis(df_raw, X, y, primary_attr, pos_label)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bias analysis error: {str(e)}")

    # SHAP
    try:
        feature_importances = compute_shap_importances(model, X, protected_list)
    except Exception as e:
        feature_importances = []

    # Gemini explanation
    try:
        gemini_text = explain_bias(
            dataset_name=file.filename or "uploaded_dataset",
            target_column=target_column,
            protected_attribute=primary_attr,
            metrics=metrics,
            feature_importances=feature_importances,
        )
    except Exception:
        gemini_text = None

    model_type = type(model).__name__
    analysis_id = str(uuid.uuid4())

    result = AnalysisResult(
        analysis_id=analysis_id,
        dataset_name=file.filename or "uploaded_dataset",
        target_column=target_column,
        protected_attributes=protected_list,
        data_profile=data_profile,
        metrics=metrics,
        feature_importances=feature_importances,
        gemini_explanation=gemini_text,
        model_type=model_type,
    )

    # Persist for mitigation + report endpoints
    store.save(
        analysis_id,
        result=result,
        df_raw=df_raw,
        X=X,
        y=y,
        model=model,
        encoders=encoders,
    )

    return result
