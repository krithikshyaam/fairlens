"""
core/profiler.py
Loads and profiles uploaded datasets.
Supports CSV, JSON, Parquet, Excel (.xlsx/.xls), TSV, Feather.
"""

import io
import pandas as pd
from models.schemas import DataProfile, ColumnProfile

PROTECTED_KEYWORDS = {
    "race", "ethnicity", "gender", "sex", "age", "religion",
    "nationality", "disability", "marital", "color",
    "origin", "pregnant", "income",
}


def load_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    ext = filename.rsplit(".", 1)[-1].lower()
    buf = io.BytesIO(file_bytes)

    if ext == "csv":
        return pd.read_csv(buf)
    elif ext == "tsv":
        return pd.read_csv(buf, sep="\t")
    elif ext == "json":
        return pd.read_json(buf)
    elif ext in ("parquet", "pq"):
        return pd.read_parquet(buf)
    elif ext in ("xlsx", "xls"):
        return pd.read_excel(buf)
    elif ext in ("feather", "ftr"):
        return pd.read_feather(buf)
    else:
        # Try CSV as fallback
        try:
            return pd.read_csv(buf)
        except Exception:
            raise ValueError(
                f"Unsupported file type: .{ext}. "
                "Supported: CSV, TSV, JSON, Parquet, Excel (.xlsx/.xls), Feather."
            )


def detect_protected_attributes(columns: list[str]) -> list[str]:
    protected = []
    for col in columns:
        col_lower = col.lower().replace("-", "_").replace(" ", "_")
        if any(kw in col_lower for kw in PROTECTED_KEYWORDS):
            protected.append(col)
    return protected


def profile_dataframe(df: pd.DataFrame, target_column: str, protected_attributes: list[str]) -> DataProfile:
    col_profiles = []

    for col in df.columns:
        is_protected = col in protected_attributes
        null_rate = round(df[col].isna().mean(), 4)
        unique_count = int(df[col].nunique())
        dtype = str(df[col].dtype)
        sample_vals = df[col].dropna().unique()[:5].tolist()
        sample_vals = [str(v) for v in sample_vals]

        col_profiles.append(ColumnProfile(
            name=col,
            dtype=dtype,
            null_rate=null_rate,
            unique_count=unique_count,
            is_protected=is_protected,
            sample_values=sample_vals,
        ))

    if target_column in df.columns:
        class_balance = df[target_column].value_counts().to_dict()
        class_balance = {str(k): int(v) for k, v in class_balance.items()}
    else:
        class_balance = {}

    auto_detected = detect_protected_attributes(list(df.columns))
    all_protected = list(set(protected_attributes + auto_detected))
    all_protected = [p for p in all_protected if p in df.columns]

    return DataProfile(
        row_count=len(df),
        column_count=len(df.columns),
        columns=col_profiles,
        class_balance=class_balance,
        protected_attributes=all_protected,
        target_column=target_column,
    )
