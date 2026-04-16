from __future__ import annotations
import pandas as pd
from scipy import stats
from analysis.context import AnalysisContext

DEPENDENCIES = ["segment_comparison"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    seg_col = ctx.results.get("segment_comparison", {}).get("data", {}).get("segment_col")
    if not seg_col:
        return {"script": "variance_analysis", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    findings: list[str] = []
    results: dict[str, dict] = {}

    for num_col in ctx.numeric_cols[:5]:
        groups = [grp.dropna().values for _, grp in df.groupby(seg_col)[num_col] if len(grp.dropna()) >= 3]
        if len(groups) < 2:
            continue
        try:
            stat, p = stats.levene(*groups)
            equal_var = p > 0.05
            results[num_col] = {
                "test": "Levene",
                "statistic": round(float(stat), 4),
                "p_value": round(float(p), 6),
                "equal_variance": equal_var,
            }
            if not equal_var:
                findings.append(
                    f"'{num_col}' has unequal variances across '{seg_col}' groups "
                    f"(Levene p={p:.4f}) — use Welch's t-test, not Student's."
                )
        except Exception:
            pass

    if not findings:
        findings.append("Variance is approximately equal across groups — standard tests are appropriate.")

    return {
        "script": "variance_analysis",
        "status": "ok",
        "findings": findings,
        "data": {"levene_results": results},
        "error": None,
    }
