from __future__ import annotations
import pandas as pd
from scipy import stats
from analysis.context import AnalysisContext

DEPENDENCIES = ["cross_tabulation"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) >= 2


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    chi2_results: list[dict] = {}

    cats = [c for c in ctx.categorical_cols if 2 <= df[c].nunique() <= 20][:4]
    tested: list[dict] = []

    for i in range(len(cats)):
        for j in range(i + 1, len(cats)):
            a, b = cats[i], cats[j]
            ct = pd.crosstab(df[a], df[b])
            try:
                chi2, p, dof, expected = stats.chi2_contingency(ct)
                cramers_v = float((chi2 / (len(df) * (min(ct.shape) - 1))) ** 0.5)
                tested.append({
                    "col_a": a, "col_b": b,
                    "chi2": round(float(chi2), 4),
                    "p_value": round(float(p), 6),
                    "dof": int(dof),
                    "cramers_v": round(cramers_v, 4),
                    "significant": p < 0.05,
                })
                if p < 0.05 and cramers_v > 0.1:
                    findings.append(
                        f"'{a}' and '{b}' are statistically dependent "
                        f"(χ²={chi2:.2f}, p={p:.4f}, V={cramers_v:.2f})."
                    )
            except Exception:
                pass

    if not findings:
        findings.append("No significant categorical dependencies detected.")

    return {
        "script": "chi_square_test",
        "status": "ok",
        "findings": findings,
        "data": {"chi2_tests": tested},
        "error": None,
    }
