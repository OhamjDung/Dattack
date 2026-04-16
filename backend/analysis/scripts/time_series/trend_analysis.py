from __future__ import annotations
import pandas as pd
import numpy as np
from scipy import stats
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    date_col = ctx.datetime_cols[0]
    findings: list[str] = []
    trends: dict[str, dict] = {}

    try:
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col]).sort_values(date_col)
    except Exception:
        return {"script": "trend_analysis", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    x = np.arange(len(df_ts))

    for col in ctx.numeric_cols[:5]:
        s = df_ts[col].dropna()
        if len(s) < 4:
            continue
        # Align indices
        valid = df_ts[col].notna()
        xi = x[valid.values]
        yi = df_ts[col][valid].values
        if len(xi) < 4:
            continue
        slope, intercept, r, p, _ = stats.linregress(xi, yi)
        direction = "upward" if slope > 0 else "downward"
        pct_change = (slope * len(xi)) / abs(yi.mean()) * 100 if yi.mean() != 0 else 0
        trends[col] = {
            "slope": round(float(slope), 6),
            "r_squared": round(float(r ** 2), 4),
            "p_value": round(float(p), 6),
            "direction": direction,
            "total_pct_change": round(float(pct_change), 2),
        }
        if p < 0.05 and abs(pct_change) > 5:
            findings.append(
                f"'{col}' has a significant {direction} trend "
                f"({pct_change:+.1f}% over the period, p={p:.4f})."
            )

    if not findings:
        findings.append("No statistically significant trends detected in numeric columns over time.")

    return {
        "script": "trend_analysis",
        "status": "ok",
        "findings": findings,
        "data": {"trends": trends, "date_col": date_col},
        "error": None,
    }
