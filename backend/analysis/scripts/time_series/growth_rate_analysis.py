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
        return {"script": "growth_rate_analysis", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    findings: list[str] = []
    growth: dict[str, dict] = {}

    for col in ctx.numeric_cols[:4]:
        s = df_ts[col].dropna()
        if len(s) < 2:
            continue
        pct_changes = s.pct_change().dropna()
        first_val, last_val = float(s.iloc[0]), float(s.iloc[-1])
        total_change = (last_val - first_val) / abs(first_val) * 100 if first_val != 0 else 0
        n_periods = len(s) - 1
        cagr = ((last_val / first_val) ** (1 / n_periods) - 1) * 100 if first_val > 0 and last_val > 0 else None
        avg_growth = float(pct_changes.mean() * 100)
        growth[col] = {
            "first_value": round(first_val, 4),
            "last_value": round(last_val, 4),
            "total_pct_change": round(total_change, 2),
            "cagr_pct": round(cagr, 3) if cagr is not None else None,
            "avg_period_growth_pct": round(avg_growth, 3),
            "periods": n_periods,
        }
        if abs(total_change) > 10:
            direction = "grew" if total_change > 0 else "declined"
            findings.append(
                f"'{col}' {direction} by {abs(total_change):.1f}% over the period"
                + (f" (CAGR={cagr:.1f}%)" if cagr is not None else "") + "."
            )

    if not findings:
        findings.append("Numeric columns show minimal growth or decline over the period.")

    return {
        "script": "growth_rate_analysis",
        "status": "ok",
        "findings": findings,
        "data": {"growth": growth},
        "error": None,
    }
