from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["cardinality_analysis"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    clusters: dict[str, list] = {}

    # Only process low-ish cardinality columns where typo detection makes sense
    target_cols = [c for c in ctx.categorical_cols if 5 <= df[c].nunique() <= 100][:3]

    for col in target_cols:
        values = [str(v) for v in df[col].dropna().unique()]
        near_dupes: list[dict] = []

        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                a, b = values[i].lower().strip(), values[j].lower().strip()
                sim = _similarity(a, b)
                if sim >= 0.8 and a != b:
                    near_dupes.append({
                        "value_a": values[i], "value_b": values[j],
                        "similarity": round(sim, 3),
                    })
                    if len(near_dupes) >= 10:
                        break
            if len(near_dupes) >= 10:
                break

        if near_dupes:
            clusters[col] = near_dupes
            for nd in near_dupes[:2]:
                findings.append(
                    f"'{col}': '{nd['value_a']}' and '{nd['value_b']}' may be the same "
                    f"(similarity={nd['similarity']:.0%}) — check for typos."
                )

    if not findings:
        findings.append("No near-duplicate category values found.")

    return {
        "script": "edit_distance_clustering",
        "status": "ok",
        "findings": findings,
        "data": {"near_duplicates": clusters},
        "error": None,
    }


def _similarity(a: str, b: str) -> float:
    # Levenshtein ratio without external library
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0.0
    matrix = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        matrix[i][0] = i
    for j in range(lb + 1):
        matrix[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + cost,
            )
    dist = matrix[la][lb]
    return 1 - dist / max(la, lb)
