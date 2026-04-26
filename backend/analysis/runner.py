from __future__ import annotations
import asyncio
import importlib
import traceback
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from analysis.context import AnalysisContext, ColumnSchema
from analysis.modules import MODULE_REGISTRY


def _load_script(dotted_path: str):
    return importlib.import_module(dotted_path)


def _build_script_map(module_names: list[str]) -> dict[str, Any]:
    scripts: dict[str, Any] = {}
    for mod_name in ["foundation"] + module_names:
        for script_name, dotted_path in MODULE_REGISTRY.get(mod_name, {}).items():
            scripts[script_name] = _load_script(dotted_path)
    return scripts


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
            for dependent in dependents[name]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

    if sum(len(w) for w in waves) != len(scripts):
        raise ValueError("Circular dependency in script graph")
    return waves


def _apply_schema(ctx: AnalysisContext) -> None:
    raw = ctx.results.get("schema_detector", {}).get("data", {}).get("columns", {})
    for col_name, col_info in raw.items():
        cs = ColumnSchema(
            name=col_name,
            inferred_type=col_info["inferred_type"],
            pandas_dtype=col_info["pandas_dtype"],
            sample_values=col_info["sample_values"],
        )
        ctx.schema[col_name] = cs
        t = col_info["inferred_type"]
        if t == "datetime":
            ctx.datetime_cols.append(col_name)
        elif t == "numeric":
            ctx.numeric_cols.append(col_name)
        elif t == "categorical":
            ctx.categorical_cols.append(col_name)
        elif t == "text":
            ctx.text_cols.append(col_name)
        elif t == "id_col":
            ctx.id_cols.append(col_name)


async def _run_wave(
    wave: list[str],
    scripts: dict[str, Any],
    ctx: AnalysisContext,
    emit: Callable[[dict], None],
    executor: ThreadPoolExecutor,
) -> None:
    loop = asyncio.get_event_loop()

    def _run_one(name: str) -> dict:
        mod = scripts[name]
        try:
            if not mod.is_applicable(ctx):
                return {"script": name, "status": "skipped", "findings": [], "data": {}, "error": None}
            result = mod.run(ctx)
            result["script"] = name
            return result
        except Exception:
            return {"script": name, "status": "error", "findings": [], "data": {},
                    "error": traceback.format_exc(limit=4)}

    futures = [loop.run_in_executor(executor, _run_one, name) for name in wave]
    results = await asyncio.gather(*futures)

    for result in results:
        ctx.results[result["script"]] = result
        emit({
            "event": "script_complete",
            "script": result["script"],
            "status": result["status"],
            "findings_count": len(result.get("findings", [])),
        })


async def run_pipeline(ctx: AnalysisContext, event_queue: asyncio.Queue) -> AnalysisContext:
    from services.gemini_service import select_modules

    def emit(event: dict) -> None:
        event_queue.put_nowait(event)

    emit({"event": "log", "message": "Running foundation analysis…"})

    foundation_scripts = _build_script_map([])
    foundation_waves = _topological_waves(foundation_scripts)

    with ThreadPoolExecutor(max_workers=4) as executor:
        for wave in foundation_waves:
            for script_name in wave:
                emit({"event": "script_running", "script": script_name})
            await _run_wave(wave, foundation_scripts, ctx, emit, executor)

    _apply_schema(ctx)
    if "field_profile" in ctx.results:
        ctx.profile = ctx.results["field_profile"]["data"].get("column_stats", {})
    if "data_quality_report" in ctx.results:
        ctx.quality = ctx.results["data_quality_report"]["data"]

    # Short-circuit if foundation flagged a critical data issue
    if ctx.abort:
        emit({"event": "log", "message": f"⚠ Aborting pipeline: {ctx.abort_reason}"})
        return ctx

    # Generate quick insights from foundation data before Phase 2 starts
    from services.gemini_service import generate_quick_insights
    loop = asyncio.get_running_loop()
    quick = await loop.run_in_executor(None, generate_quick_insights, ctx)
    for node_dict, edge_dict in quick:
        emit({"event": "node_add", "node": node_dict, "edge": edge_dict})

    emit({"event": "log", "message": "Selecting analysis modules…"})
    ctx.active_modules = await select_modules(ctx.to_gemini_summary(), ctx.goal)
    emit({"event": "modules_selected", "modules": ctx.active_modules,
          "message": f"Modules selected: {', '.join(ctx.active_modules)}"})

    all_scripts = _build_script_map(ctx.active_modules)
    waves = _topological_waves(all_scripts)
    total = len(waves)

    with ThreadPoolExecutor(max_workers=8) as executor:
        for i, wave in enumerate(waves):
            if ctx.abort:
                emit({"event": "log", "message": f"⚠ Aborting remaining waves: {ctx.abort_reason}"})
                break
            emit({"event": "log",
                  "message": f"Wave {i+1}/{total}: {', '.join(wave)}"})
            for script_name in wave:
                emit({"event": "script_running", "script": script_name})
            await _run_wave(wave, all_scripts, ctx, emit, executor)

    emit({"event": "log", "message": "All scripts complete. Synthesising findings…"})
    return ctx
