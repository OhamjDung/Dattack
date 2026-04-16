from __future__ import annotations
import re
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = []


def is_applicable(ctx: AnalysisContext) -> bool:
    return True


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    columns: dict[str, dict] = {}

    for col in df.columns:
        series = df[col]
        inferred = _infer_type(series, col)
        columns[col] = {
            "inferred_type": inferred,
            "pandas_dtype": str(series.dtype),
            "sample_values": series.dropna().head(5).tolist(),
            "null_count": int(series.isna().sum()),
            "unique_count": int(series.nunique()),
        }

    findings = []
    datetime_cols = [c for c, v in columns.items() if v["inferred_type"] == "datetime"]
    numeric_cols  = [c for c, v in columns.items() if v["inferred_type"] == "numeric"]
    cat_cols      = [c for c, v in columns.items() if v["inferred_type"] == "categorical"]
    text_cols     = [c for c, v in columns.items() if v["inferred_type"] == "text"]
    id_cols       = [c for c, v in columns.items() if v["inferred_type"] == "id_col"]

    findings.append(
        f"Dataset has {len(df):,} rows × {len(df.columns)} columns: "
        f"{len(numeric_cols)} numeric, {len(cat_cols)} categorical, "
        f"{len(datetime_cols)} datetime, {len(text_cols)} text, {len(id_cols)} ID."
    )
    if datetime_cols:
        findings.append(f"Time columns detected: {', '.join(datetime_cols)}.")

    return {
        "script": "schema_detector",
        "status": "ok",
        "findings": findings,
        "data": {"columns": columns},
        "error": None,
    }


def _infer_type(series: pd.Series, col_name: str) -> str:
    name_lower = col_name.lower()
    n = len(series)
    non_null = series.dropna()

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_numeric_dtype(series):
        unique_ratio = series.nunique() / max(n, 1)
        if unique_ratio > 0.95 and series.nunique() > 50:
            return "id_col"
        return "numeric"

    # Object / string columns
    if pd.api.types.is_object_dtype(series):
        # Try parsing as datetime
        try:
            sample = non_null.head(30)
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().mean() > 0.8:
                return "datetime"
        except Exception:
            pass

        unique_ratio = series.nunique() / max(n, 1)
        avg_len = non_null.astype(str).str.len().mean() if len(non_null) > 0 else 0

        # High cardinality long strings → text
        if unique_ratio > 0.5 and avg_len > 30:
            return "text"

        # Near-unique short strings → id_col
        id_patterns = ["id", "uuid", "key", "code", "ref", "sku"]
        if unique_ratio > 0.9 and any(p in name_lower for p in id_patterns):
            return "id_col"

        # Low cardinality → categorical
        return "categorical"

    return "categorical"
