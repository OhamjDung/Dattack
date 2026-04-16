from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return True


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []

    exact_dups = int(df.duplicated().sum())
    exact_rate = exact_dups / max(len(df), 1)

    # Near-duplicate: duplicates on non-ID non-date columns
    key_cols = [c for c in df.columns
                if c not in ctx.id_cols and c not in ctx.datetime_cols][:10]
    near_dups = int(df.duplicated(subset=key_cols).sum()) if key_cols else 0
    near_rate = near_dups / max(len(df), 1)

    if exact_dups > 0:
        findings.append(f"{exact_dups:,} exact duplicate rows ({exact_rate:.1%}) — safe to drop.")
    if near_dups > exact_dups:
        findings.append(
            f"{near_dups:,} near-duplicate rows ({near_rate:.1%}) on non-ID columns — review before dropping."
        )
    if not findings:
        findings.append("No duplicate rows detected.")

    return {
        "script": "duplicate_detection",
        "status": "ok",
        "findings": findings,
        "data": {
            "exact_duplicate_count": exact_dups,
            "exact_duplicate_rate": round(exact_rate, 4),
            "near_duplicate_count": near_dups,
            "near_duplicate_rate": round(near_rate, 4),
        },
        "error": None,
    }
