from __future__ import annotations
import asyncio
import io
import json
import os
from typing import AsyncGenerator, Any

import pandas as pd

from analysis.context import AnalysisContext
from analysis.runner import run_pipeline
from services.gemini_service import stream_synthesis


def _is_mock_mode() -> bool:
    return os.environ.get("MOCK_MODE", "").strip().lower() in ("1", "true", "yes")


async def _stream_mock_analysis(goal: str) -> AsyncGenerator[dict, None]:
    mock_goal = goal or "Mock analysis goal"

    yield {"event": "log", "data": json.dumps({"message": "MOCK_MODE is enabled: bypassing analysis pipeline."})}
    yield {"event": "log", "data": json.dumps({"message": f"Goal: {mock_goal}"})}

    findings = [
        (
            "Top Segment Leads",
            "Mock result: Enterprise segment contributes 44% of total revenue while representing 18% of customers.",
            0.93,
        ),
        (
            "Seasonal Spike",
            "Mock result: Revenue peaks in Q4 at 1.6x the annual monthly average.",
            0.89,
        ),
        (
            "Concentration Risk",
            "Mock result: Top 10 accounts generate 58% of revenue, indicating moderate concentration exposure.",
            0.87,
        ),
    ]

    for index, (label, description, confidence) in enumerate(findings):
        node_id = f"finding-{index}"
        node = {
            "id": node_id,
            "type": "findingNode",
            "position": {"x": 780, "y": 120 + (index + 1) * 190},
            "data": {
                "label": label,
                "description": description,
                "type": "finding",
                "status": "complete",
                "metadata": {"confidence": confidence, "source": "mock_stream"},
            },
        }
        edge = {
            "id": f"e-goal-{node_id}",
            "source": "goal-1",
            "target": node_id,
            "animated": True,
        }
        yield {"event": "node_add", "data": json.dumps({"node": node, "edge": edge})}
        await asyncio.sleep(0.05)

    yield {
        "event": "complete",
        "data": json.dumps(
            {
                "summary": (
                    "Mock analysis complete. Findings were generated without running foundation or module scripts. "
                    "Disable MOCK_MODE to execute the full analysis pipeline."
                )
            }
        ),
    }


async def run_and_stream(session_data: dict[str, Any]) -> AsyncGenerator[dict, None]:
    csv_bytes: bytes = session_data.get("csv_bytes", b"")
    goal: str = session_data.get("goal", "")
    target_col: str | None = session_data.get("target_col")

    if _is_mock_mode():
        async for event in _stream_mock_analysis(goal):
            yield event
        return

    if not csv_bytes:
        yield {"event": "error", "data": json.dumps({"message": "No CSV data found in session."})}
        return

    try:
        df = pd.read_csv(io.BytesIO(csv_bytes))
    except Exception as e:
        yield {"event": "error", "data": json.dumps({"message": f"Failed to parse CSV: {e}"})}
        return

    ctx = AnalysisContext(df=df, goal=goal, target_col=target_col)
    event_queue: asyncio.Queue = asyncio.Queue()

    pipeline_task = asyncio.create_task(_run_pipeline_task(ctx, event_queue))

    while True:
        try:
            event = await asyncio.wait_for(event_queue.get(), timeout=180.0)
        except asyncio.TimeoutError:
            yield {"event": "error", "data": json.dumps({"message": "Pipeline timed out."})}
            pipeline_task.cancel()
            return

        etype = event.get("event")

        if etype == "__done__":
            print(f"[SSE] pipeline done", flush=True)
            break
        elif etype == "__error__":
            print(f"[SSE] pipeline error: {event.get('error', '')[:200]}", flush=True)
            yield {"event": "error", "data": json.dumps({"message": event.get("error", "Unknown error")})}
            return
        elif etype == "log":
            print(f"[SSE] log: {event.get('message', '')}", flush=True)
            yield {"event": "log", "data": json.dumps({"message": event.get("message", "")})}
        elif etype == "script_complete":
            status = event.get("status", "ok")
            script = event.get("script", "")
            findings_count = event.get("findings_count", 0)
            icon = "✓" if status == "ok" else "⚠" if status == "skipped" else "✗"
            msg = f"{icon} {script}"
            if findings_count:
                msg += f" ({findings_count} finding{'s' if findings_count != 1 else ''})"
            yield {"event": "log", "data": json.dumps({"message": msg})}
            yield {"event": "script_complete", "data": json.dumps({"script": script, "status": status})}
        elif etype == "node_add":
            yield {"event": "node_add", "data": json.dumps(
                {"node": event["node"], "edge": event["edge"]}
            )}
        elif etype == "script_running":
            print(f"[SSE] script_running: {event.get('script', '')}", flush=True)
            yield {"event": "script_running", "data": json.dumps(
                {"script": event.get("script", "")}
            )}
        elif etype == "modules_selected":
            modules = event.get("modules", [])
            yield {"event": "log", "data": json.dumps(
                {"message": f"Running modules: {', '.join(modules)}"}
            )}
        else:
            yield {"event": "log", "data": json.dumps({"message": str(event.get("message", ""))})}

    # Pipeline done — stream Gemini synthesis
    try:
        async for sse_event in stream_synthesis(ctx):
            yield sse_event
    except Exception as e:
        import traceback
        err = traceback.format_exc(limit=3)
        print(f"[SSE] synthesis error: {err[:300]}", flush=True)
        yield {"event": "log", "data": json.dumps({"message": f"⚠ Synthesis error: {type(e).__name__}: {str(e)[:120]}"})}
        yield {"event": "complete", "data": json.dumps({"summary": "Analysis scripts completed. Synthesis failed — check logs."})}


async def _run_pipeline_task(ctx: AnalysisContext, queue: asyncio.Queue) -> None:
    try:
        await run_pipeline(ctx, queue)
        await queue.put({"event": "__done__"})
    except Exception as e:
        import traceback
        await queue.put({"event": "__error__", "error": traceback.format_exc(limit=5)})
