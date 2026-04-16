from __future__ import annotations
import numpy as np
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["correlation_matrix"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) >= 3


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    cols = [c for c in ctx.numeric_cols if df[c].nunique() > 1]
    if len(cols) < 3:
        return {"script": "multicollinearity_check", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    num_df = df[cols].dropna()
    if len(num_df) < len(cols) + 2:
        return {"script": "multicollinearity_check", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    from numpy.linalg import lstsq
    vif_scores: dict[str, float] = {}
    for i, col in enumerate(cols):
        y = num_df[col].values
        X = num_df.drop(columns=[col]).values
        X = np.column_stack([np.ones(len(X)), X])
        try:
            _, res, rank, _ = lstsq(X, y, rcond=None)
            ss_res = float(np.sum((y - X @ lstsq(X, y, rcond=None)[0]) ** 2))
            ss_tot = float(np.sum((y - y.mean()) ** 2))
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            vif = 1 / (1 - r2) if r2 < 1 else float("inf")
            vif_scores[col] = round(vif, 2)
        except Exception:
            vif_scores[col] = float("nan")

    high_vif = {c: v for c, v in vif_scores.items() if v > 5}
    findings: list[str] = []
    for col, vif in sorted(high_vif.items(), key=lambda x: -x[1])[:5]:
        findings.append(f"'{col}' has VIF={vif:.1f} — high multicollinearity with other numeric features.")
    if not findings:
        findings.append("No multicollinearity issues detected (all VIF < 5).")

    return {
        "script": "multicollinearity_check",
        "status": "ok",
        "findings": findings,
        "data": {"vif_scores": vif_scores, "high_vif_threshold": 5},
        "error": None,
    }
