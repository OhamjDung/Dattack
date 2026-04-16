from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    date_col = ctx.datetime_cols[0]

    try:
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    except Exception:
        return {"script": "peak_valley_detection", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    findings: list[str] = []
    peaks_data: dict[str, dict] = {}

    for col in ctx.numeric_cols[:3]:
        s = df_ts[col].dropna().reset_index(drop=True)
        if len(s) < 5:
            continue
        # Simple local maxima/minima detection
        peaks = [i for i in range(1, len(s) - 1) if s[i] > s[i-1] and s[i] > s[i+1]]
        valleys = [i for i in range(1, len(s) - 1) if s[i] < s[i-1] and s[i] < s[i+1]]
        if not peaks and not valleys:
            continue
        max_peak_val = float(s.iloc[peaks].max()) if peaks else None
        min_valley_val = float(s.iloc[valleys].min()) if valleys else None
        swing = (max_peak_val - min_valley_val) if (max_peak_val and min_valley_val) else None
        swing_pct = swing / abs(s.mean()) * 100 if (swing and s.mean() != 0) else None

        peaks_data[col] = {
            "peak_count": len(peaks),
            "valley_count": len(valleys),
            "max_peak": max_peak_val,
            "min_valley": min_valley_val,
            "swing_pct": round(swing_pct, 1) if swing_pct else None,
        }
        if swing_pct and swing_pct > 30:
            findings.append(
                f"'{col}' has {len(peaks)} peaks and {len(valleys)} valleys "
                f"with a {swing_pct:.0f}% peak-to-valley swing."
            )

    if not findings:
        findings.append("No significant peaks or valleys detected in the time series.")

    return {
        "script": "peak_valley_detection",
        "status": "ok",
        "findings": findings,
        "data": {"peaks": peaks_data},
        "error": None,
    }
