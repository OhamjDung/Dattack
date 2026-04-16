from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["categorical_frequency", "trend_analysis"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0 and len(ctx.categorical_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    date_col = ctx.datetime_cols[0]

    try:
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col]).sort_values(date_col)
    except Exception:
        return {"script": "category_drift", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    findings: list[str] = []
    drift: dict[str, dict] = {}

    half = len(df_ts) // 2

    for col in ctx.categorical_cols[:3]:
        if df_ts[col].nunique() > 20:
            continue
        early = df_ts.iloc[:half][col].value_counts(normalize=True)
        late = df_ts.iloc[half:][col].value_counts(normalize=True)
        all_cats = set(early.index) | set(late.index)
        changes: list[dict] = []
        for cat in all_cats:
            e = float(early.get(cat, 0))
            l = float(late.get(cat, 0))
            delta = l - e
            if abs(delta) > 0.05:
                changes.append({"category": str(cat), "early_share": round(e, 4),
                                 "late_share": round(l, 4), "delta": round(delta, 4)})
        changes.sort(key=lambda x: abs(x["delta"]), reverse=True)
        drift[col] = {"changes": changes[:5]}
        for c in changes[:2]:
            direction = "growing" if c["delta"] > 0 else "shrinking"
            findings.append(
                f"'{col}' = '{c['category']}' is {direction} in share "
                f"({c['early_share']:.1%} → {c['late_share']:.1%})."
            )

    if not findings:
        findings.append("Category distributions are stable over time — no significant drift.")

    return {
        "script": "category_drift",
        "status": "ok",
        "findings": findings,
        "data": {"drift": drift},
        "error": None,
    }
