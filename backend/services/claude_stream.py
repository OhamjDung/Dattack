import anthropic
import json
from typing import AsyncGenerator, Any

async_client = anthropic.AsyncAnthropic()

RECORD_FINDING_TOOL: dict = {
    "name": "record_finding",
    "description": "Record a key finding or insight discovered during analysis as a map node",
    "input_schema": {
        "type": "object",
        "properties": {
            "label": {
                "type": "string",
                "description": "Short finding title (5–8 words)",
            },
            "description": {
                "type": "string",
                "description": "1–2 sentences describing what was found",
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score 0–1",
            },
        },
        "required": ["label", "description", "confidence"],
    },
}


async def stream_analysis(session_data: dict[str, Any]) -> AsyncGenerator[dict, None]:
    nodes: list[dict] = session_data.get("nodes", [])
    goal: str = session_data.get("goal", "")

    map_description = "\n".join(
        f"  - {n['data']['type']}: {n['data']['label']} — {n['data']['description']}"
        for n in nodes
    )

    prompt = f"""You are a data analysis consultant performing a live analysis session.

Analysis goal: {goal}

Map of data and techniques:
{map_description}

Walk through your analysis step by step, thinking out loud. As you reason:
- Explain your analytical process naturally
- Call record_finding() each time you identify a significant insight, pattern, correlation, anomaly, or trend
- Be specific — reference the actual datasets and goal above

Aim to surface 2–4 meaningful findings."""

    finding_index = 0
    in_tool_block = False
    tool_input_buf = ""
    text_buf = ""

    async with async_client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        tools=[RECORD_FINDING_TOOL],
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        async for event in stream:
            etype = event.type  # type: ignore[attr-defined]

            if etype == "content_block_start":
                block = event.content_block  # type: ignore[attr-defined]
                if block.type == "tool_use":
                    in_tool_block = True
                    tool_input_buf = ""
                    # flush any pending text
                    if text_buf.strip():
                        yield {"event": "log", "data": json.dumps({"message": text_buf.strip()})}
                        text_buf = ""
                else:
                    in_tool_block = False

            elif etype == "content_block_delta":
                delta = event.delta  # type: ignore[attr-defined]
                if hasattr(delta, "text"):
                    text_buf += delta.text
                    # emit on sentence boundaries to avoid tiny fragments
                    while any(text_buf.endswith(p) for p in (".", "!", "?", "\n")):
                        sentence, _, text_buf = text_buf.partition(
                            next(p for p in (".", "!", "?", "\n") if text_buf.endswith(p))
                        )
                        msg = (sentence + _).strip()
                        if msg:
                            yield {"event": "log", "data": json.dumps({"message": msg})}
                        break
                elif hasattr(delta, "partial_json"):
                    tool_input_buf += delta.partial_json

            elif etype == "content_block_stop" and in_tool_block:
                try:
                    tool_data = json.loads(tool_input_buf)
                    fid = f"finding-{finding_index}"
                    finding_index += 1
                    node = {
                        "id": fid,
                        "type": "findingNode",
                        "position": {"x": 780, "y": 120 + finding_index * 190},
                        "data": {
                            "label": tool_data["label"],
                            "description": tool_data["description"],
                            "type": "finding",
                            "status": "complete",
                            "metadata": {"confidence": tool_data.get("confidence", 0.8)},
                        },
                    }
                    edge = {
                        "id": f"e-goal-{fid}",
                        "source": "goal-1",
                        "target": fid,
                        "animated": True,
                    }
                    yield {"event": "node_add", "data": json.dumps({"node": node, "edge": edge})}
                except (json.JSONDecodeError, KeyError):
                    pass
                in_tool_block = False

        # flush remaining text
        if text_buf.strip():
            yield {"event": "log", "data": json.dumps({"message": text_buf.strip()})}

    yield {
        "event": "complete",
        "data": json.dumps(
            {"summary": f"Analysis complete. Found {finding_index} key insight{'s' if finding_index != 1 else ''}."}
        ),
    }
