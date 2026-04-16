from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["categorical_frequency"]


def is_applicable(ctx: AnalysisContext) -> bool:
    # Need a column that looks like ordered stages
    df = ctx.df
    for col in ctx.categorical_cols:
        if df[col].nunique() <= 8:
            return True
    return False


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    funnels: list[dict] = {}

    stage_col = next(
        (c for c in ctx.categorical_cols if 2 <= df[c].nunique() <= 8), None
    )
    if not stage_col:
        return {"script": "funnel_analysis", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    vc = df[stage_col].value_counts()
    total = int(vc.sum())
    stages = []
    prev_count = total
    for stage, count in vc.items():
        count = int(count)
        conv = round(count / prev_count, 4) if prev_count > 0 else 0
        drop = round(1 - conv, 4)
        stages.append({
            "stage": str(stage), "count": count,
            "pct_of_total": round(count / total, 4),
            "conversion_from_prev": conv,
            "drop_off": drop,
        })
        prev_count = count

    for s in stages:
        if s["drop_off"] > 0.3:
            findings.append(
                f"High drop-off at '{s['stage']}': {s['drop_off']:.1%} lost "
                f"({s['count']:,} remaining)."
            )

    if not findings:
        findings.append(f"'{stage_col}' funnel shows balanced conversion across stages.")

    return {
        "script": "funnel_analysis",
        "status": "ok",
        "findings": findings,
        "data": {"funnel_col": stage_col, "stages": stages},
        "error": None,
    }
