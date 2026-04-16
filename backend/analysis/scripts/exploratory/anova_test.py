from __future__ import annotations
import pandas as pd
from scipy import stats
from analysis.context import AnalysisContext

DEPENDENCIES = ["segment_comparison", "normality_tests"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    seg_col = ctx.results.get("segment_comparison", {}).get("data", {}).get("segment_col")
    if not seg_col or df[seg_col].nunique() < 2:
        return {"script": "anova_test", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    findings: list[str] = []
    anova_results: dict[str, dict] = {}

    for num_col in ctx.numeric_cols[:5]:
        groups = [grp.dropna().values for _, grp in df.groupby(seg_col)[num_col]
                  if len(grp.dropna()) >= 3]
        if len(groups) < 2:
            continue
        try:
            stat, p = stats.f_oneway(*groups)
            anova_results[num_col] = {
                "f_statistic": round(float(stat), 4),
                "p_value": round(float(p), 6),
                "significant": p < 0.05,
            }
            if p < 0.05:
                findings.append(
                    f"'{num_col}' differs significantly across '{seg_col}' groups "
                    f"(ANOVA F={stat:.2f}, p={p:.4f})."
                )
        except Exception:
            pass

    if not findings:
        findings.append(f"No significant mean differences found across '{seg_col}' groups.")

    return {
        "script": "anova_test",
        "status": "ok",
        "findings": findings,
        "data": {"anova": anova_results, "segment_col": seg_col},
        "error": None,
    }
