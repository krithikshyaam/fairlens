"""
core/encoder.py
Encodes features for ML model training and bias analysis.
Handles categorical encoding, missing values, feature/target splitting.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder


def encode_dataframe(
    df: pd.DataFrame,
    target_column: str,
    protected_attributes: list[str],
) -> tuple[pd.DataFrame, pd.Series, dict[str, LabelEncoder]]:
    """
    Encode a raw dataframe for ML use.

    Returns:
        X           - feature matrix (encoded, no target)
        y           - target series (numeric)
        encoders    - dict of LabelEncoders used, keyed by column name
    """
    df = df.copy()

    # Drop rows with null target
    df = df.dropna(subset=[target_column])

    encoders: dict[str, LabelEncoder] = {}

    # Encode feature columns but NOT the target.
    # sklearn classifiers handle string labels natively, so keeping y as
    # original values ('high'/'low', 0/1) avoids encoding-mismatch bugs
    # when compute_metrics compares predictions to positive_label.
    for col in df.columns:
        if col == target_column:
            continue
        if df[col].dtype == object or str(df[col].dtype) == "category":
            le = LabelEncoder()
            df[col] = df[col].astype(str)
            df[col] = le.fit_transform(df[col])
            encoders[col] = le

    # Fill remaining nulls with median (numeric cols only)
    df = df.fillna(df.median(numeric_only=True))

    y = df[target_column]          # original values — string or numeric
    X = df.drop(columns=[target_column])

    return X, y, encoders


def get_protected_series(
    df: pd.DataFrame,
    protected_attribute: str,
) -> pd.Series:
    """
    Return the raw (un-encoded) protected attribute series,
    with NaN rows dropped, index aligned with df.
    """
    df = df.dropna(subset=[protected_attribute])
    return df[protected_attribute].astype(str)
