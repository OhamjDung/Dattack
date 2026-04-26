from __future__ import annotations
import asyncio
import io
import json
from typing import AsyncGenerator, Any

import pandas as pd

from analysis.context import AnalysisContext
from analysis.runner import run_pipeline
from services.gemini_service import stream_synthesis


async def run_and_stream(session_data: dict[str, Any]) -> AsyncGenerator[dict, None]:
    csv_bytes: bytes = session_data.get("csv_bytes", b"")
    goal: str = session_data.get("goal", "")
    target_col: str | None = session_data.get("target_col")

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
    async for sse_event in stream_synthesis(ctx):
        yield sse_event


async def _run_pipeline_task(ctx: AnalysisContext, queue: asyncio.Queue) -> None:
    try:
        await run_pipeline(ctx, queue)
        await queue.put({"event": "__done__"})
    except Exception as e:
        import traceback
        await queue.put({"event": "__error__", "error": traceback.format_exc(limit=5)})
