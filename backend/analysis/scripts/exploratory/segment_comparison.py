from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "field_profile", "categorical_frequency"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    segments: list[dict] = []

    # Use first categorical col with 2-10 unique values as segmenter
    seg_col = next(
        (c for c in ctx.categorical_cols if 2 <= df[c].nunique() <= 10), None
    )
    if seg_col is None:
        return {"script": "segment_comparison", "status": "skipped",
                "findings": ["No suitable segmentation column found (need 2–10 unique values)."],
                "data": {}, "error": None}

    target_cols = ctx.numeric_cols[:4]
    for num_col in target_cols:
        group_stats = df.groupby(seg_col)[num_col].agg(["mean", "median", "std", "count"])
        overall_mean = df[num_col].mean()
        group_stats["pct_diff_from_mean"] = ((group_stats["mean"] - overall_mean) / abs(overall_mean) * 100).round(1)

        top_group = group_stats["mean"].idxmax()
        bot_group = group_stats["mean"].idxmin()
        spread = group_stats["mean"].max() - group_stats["mean"].min()
        relative_spread = spread / abs(overall_mean) if overall_mean != 0 else 0

        seg_result = {
            "segment_col": seg_col,
            "metric_col": num_col,
            "group_stats": group_stats.reset_index().to_dict(orient="records"),
            "top_group": str(top_group),
            "bottom_group": str(bot_group),
            "relative_spread": round(float(relative_spread), 3),
        }
        segments.append(seg_result)

        if relative_spread > 0.3:
            findings.append(
                f"'{num_col}' varies significantly across '{seg_col}': "
                f"'{top_group}' is highest, '{bot_group}' is lowest "
                f"(spread={relative_spread:.0%} of mean)."
            )

    if not findings:
        findings.append(f"'{seg_col}' segments show similar numeric distributions — minimal segmentation effect.")

    return {
        "script": "segment_comparison",
        "status": "ok",
        "findings": findings,
        "data": {"segments": segments, "segment_col": seg_col},
        "error": None,
    }
