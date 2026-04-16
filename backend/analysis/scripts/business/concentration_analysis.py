from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["pareto_analysis"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    concentration: dict[str, dict] = {}

    for col in ctx.numeric_cols[:3]:
        s = df[col].dropna()
        s = s[s > 0]
        if len(s) < 4:
            continue
        # Herfindahl-Hirschman Index
        shares = s / s.sum()
        hhi = float((shares ** 2).sum())
        # CR5 — top 5 share
        cr5 = float(s.nlargest(5).sum() / s.sum())
        concentration[col] = {
            "hhi": round(hhi, 6),
            "cr5": round(cr5, 4),
            "hhi_label": "highly concentrated" if hhi > 0.25 else
                         "moderately concentrated" if hhi > 0.1 else "competitive",
        }
        if hhi > 0.15:
            findings.append(
                f"'{col}' is {concentration[col]['hhi_label']} "
                f"(HHI={hhi:.4f}, top-5 share={cr5:.1%})."
            )

    if not findings:
        findings.append("Metrics show competitive (low concentration) distributions.")

    return {
        "script": "concentration_analysis",
        "status": "ok",
        "findings": findings,
        "data": {"concentration": concentration},
        "error": None,
    }
