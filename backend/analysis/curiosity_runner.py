from __future__ import annotations
import asyncio
import importlib
import traceback
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from analysis.context import AnalysisContext

CURIOSITY_REGISTRY: dict[str, str] = {
    # foundation (reused)
    "schema_detector":     "analysis.scripts.foundation.schema_detector",
    "field_profile":       "analysis.scripts.foundation.field_profile",
    "data_quality_report": "analysis.scripts.foundation.data_quality_report",
    # structure
    "entity_type_guesser":      "analysis.curiosity_scripts.structure.entity_type_guesser",
    "target_col_candidates":    "analysis.curiosity_scripts.structure.target_col_candidates",
    "column_role_classifier":   "analysis.curiosity_scripts.structure.column_role_classifier",
    "dataset_shape_classifier": "analysis.curiosity_scripts.structure.dataset_shape_classifier",
    "join_key_candidates":      "analysis.curiosity_scripts.structure.join_key_candidates",
    "boolean_disguise_detector":"analysis.curiosity_scripts.structure.boolean_disguise_detector",
    "id_column_validator":      "analysis.curiosity_scripts.structure.id_column_validator",
    # signals
    "null_intent_detector":        "analysis.curiosity_scripts.signals.null_intent_detector",
    "outlier_prevalence_screen":   "analysis.curiosity_scripts.signals.outlier_prevalence_screen",
    "correlation_opportunity":     "analysis.curiosity_scripts.signals.correlation_opportunity",
    "segment_variable_candidates": "analysis.curiosity_scripts.signals.segment_variable_candidates",
    "temporal_coverage_analyzer":  "analysis.curiosity_scripts.signals.temporal_coverage_analyzer",
    "concentration_screen":        "analysis.curiosity_scripts.signals.concentration_screen",
    "growth_signal_screen":        "analysis.curiosity_scripts.signals.growth_signal_screen",
    "anomaly_prevalence_screen":   "analysis.curiosity_scripts.signals.anomaly_prevalence_screen",
    "cardinality_screen":          "analysis.curiosity_scripts.signals.cardinality_screen",
    # hypotheses
    "analysis_hypothesis_builder":  "analysis.curiosity_scripts.hypotheses.analysis_hypothesis_builder",
    "missing_analysis_detector":    "analysis.curiosity_scripts.hypotheses.missing_analysis_detector",
    "composite_metric_opportunity": "analysis.curiosity_scripts.hypotheses.composite_metric_opportunity",
    "benchmark_opportunity_detector":"analysis.curiosity_scripts.hypotheses.benchmark_opportunity_detector",
}


def _load(dotted: str):
    return importlib.import_module(dotted)


def _topological_waves(scripts: dict[str, Any]) -> list[list[str]]:
    in_degree: dict[str, int] = {n: 0 for n in scripts}
    dependents: dict[str, list[str]] = defaultdict(list)

    for name, mod in scripts.items():
        for dep in getattr(mod, "DEPENDENCIES", []):
            if dep in scripts:
                in_degree[name] += 1
                dependents[dep].append(name)

    queue = deque(n for n, d in in_degree.items() if d == 0)
    waves: list[list[str]] = []
    while queue:
        wave = list(queue)
        waves.append(wave)
        queue.clear()
        for name in wave:
            for dep in dependents[name]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

    if sum(len(w) for w in waves) != len(scripts):
        raise ValueError("Circular dependency in curiosity script graph")
    return waves


def _sample_diverse_rows(ctx: AnalysisContext, max_rows: int = 8) -> list[dict]:
    """Pick semantically diverse rows: min/median/max for numeric cols, top categories for categorical."""
    df = ctx.df
    if df.empty:
        return []

    selected_indices: set[int] = set()

    for col in ctx.numeric_cols[:3]:
        try:
            col_clean = df[col].dropna()
            if col_clean.empty:
                continue
            selected_indices.add(int(col_clean.idxmin()))
            selected_indices.add(int(col_clean.index[len(col_clean) // 2]))
            selected_indices.add(int(col_clean.idxmax()))
        except Exception:
            continue

    for col in ctx.categorical_cols[:2]:
        try:
            top_vals = df[col].value_counts().head(3).index
            for val in top_vals:
                matches = df.index[df[col] == val].tolist()
                if matches:
                    selected_indices.add(int(matches[0]))
        except Exception:
            continue

    indices = sorted(selected_indices)[:max_rows]
    if not indices:
        indices = list(range(min(3, len(df))))

    rows = df.iloc[indices].fillna("").astype(str)
    return rows.to_dict(orient="records")


def _apply_schema(ctx: AnalysisContext) -> None:
    from analysis.runner import _apply_schema as _base_apply_schema
    _base_apply_schema(ctx)


async def run_curiosity_pipeline(ctx: AnalysisContext) -> dict[str, Any]:
    """Run all curiosity scripts and return aggregated question/technique candidates."""
    scripts = {name: _load(path) for name, path in CURIOSITY_REGISTRY.items()}
    waves = _topological_waves(scripts)
    loop = asyncio.get_event_loop()

    def _run_one(name: str) -> dict:
        mod = scripts[name]
        try:
            if not mod.is_applicable(ctx):
                return {"script": name, "status": "skipped",
                        "question_candidates": [], "technique_candidates": [], "data": {}, "findings": []}
            result = mod.run(ctx)
            result.setdefault("question_candidates", [])
            result.setdefault("technique_candidates", [])
            result.setdefault("findings", [])
            result["script"] = name
            return result
        except Exception:
            return {"script": name, "status": "error",
                    "question_candidates": [], "technique_candidates": [],
                    "findings": [], "data": {}, "error": traceback.format_exc(limit=4)}

    with ThreadPoolExecutor(max_workers=8) as executor:
        for wave in waves:
            futures = [loop.run_in_executor(executor, _run_one, name) for name in wave]
            results = await asyncio.gather(*futures)
            for r in results:
                ctx.results[r["script"]] = r
            # Apply schema after foundation wave
            if "schema_detector" in wave:
                _apply_schema(ctx)
            if "field_profile" in wave and "field_profile" in ctx.results:
                ctx.profile = ctx.results["field_profile"]["data"].get("column_stats", {})

    # Aggregate all candidates
    all_questions: list[dict] = []
    all_techniques: list[dict] = []

    for name, result in ctx.results.items():
        if result.get("status") == "ok":
            all_questions.extend(result.get("question_candidates", []))
            all_techniques.extend(result.get("technique_candidates", []))

    # Deduplicate by label (keep highest confidence)
    def dedup(items: list[dict]) -> list[dict]:
        seen: dict[str, dict] = {}
        for item in items:
            label = item["label"]
            if label not in seen or item["confidence"] > seen[label]["confidence"]:
                seen[label] = item
        return sorted(seen.values(), key=lambda x: -x["confidence"])

    return {
        "question_candidates": dedup(all_questions),
        "technique_candidates": dedup(all_techniques),
        "data_summary": ctx.to_gemini_summary(),
        "sampled_rows": _sample_diverse_rows(ctx),
    }
