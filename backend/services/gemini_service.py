from __future__ import annotations
import json
import os
import re
import uuid
from typing import AsyncGenerator

from google import genai
from google.genai import types

from schemas.models import Node, Edge, NodeData, NodePosition

_MODEL = "gemini-2.0-flash"
_client: "genai.Client | None" = None


def _get_client() -> "genai.Client":
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=api_key)
    return _client

REACT_TYPE_MAP = {
    "goal": "goalNode",
    "data_source": "dataSourceNode",
    "technique": "techniqueNode",
    "question": "questionNode",
    "finding": "findingNode",
}

_LAYOUT: dict[str, tuple[int, int]] = {
    "goal": (450, 300),
    "data_source": (100, 0),
    "technique": (450, 0),
    "question": (780, 0),
    "finding": (780, 0),
}


def _position(node_type: str, index: int) -> NodePosition:
    bx, _ = _LAYOUT.get(node_type, (300, 0))
    if node_type == "goal":
        return NodePosition(x=bx, y=300)
    return NodePosition(x=bx, y=120 + index * 190)


def _parse_json_nodes(text: str) -> tuple[list[Node], list[Edge]]:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return [], []
    raw = json.loads(match.group())
    type_counts: dict[str, int] = {}
    nodes: list[Node] = []
    for n in raw.get("nodes", []):
        nt: str = n.get("node_type", "technique")
        idx = type_counts.get(nt, 0)
        type_counts[nt] = idx + 1
        nodes.append(Node(
            id=n["id"],
            type=REACT_TYPE_MAP.get(nt, "custom"),
            position=_position(nt, idx),
            data=NodeData(
                label=n["label"],
                description=n["description"],
                type=nt,  # type: ignore[arg-type]
                status=n.get("status", "active"),  # type: ignore[arg-type]
                metadata=n.get("metadata"),
            ),
        ))
    edges = [
        Edge(id=e["id"], source=e["source"], target=e["target"], animated=True)
        for e in raw.get("edges", [])
    ]
    return nodes, edges


def _map_prompt(nodes_spec: str) -> str:
    return f"""Return ONLY a JSON object (no markdown, no explanation) with this exact structure:
{{
  "nodes": [
    {{"id": "...", "node_type": "goal|data_source|technique|question", "label": "...", "description": "...", "status": "active"}}
  ],
  "edges": [
    {{"id": "...", "source": "node-id", "target": "node-id"}}
  ]
}}

{nodes_spec}"""


def generate_initial_map(
    goal: str,
    why: str,
    available_data: str,
    ideas: str,
    curiosity_outputs: dict | None = None,
) -> tuple[list[Node], list[Edge]]:
    if curiosity_outputs:
        questions_text = "\n".join(
            f"  - [{q['confidence']:.0%}] {q['label']}: {q['description']}"
            for q in curiosity_outputs.get("question_candidates", [])[:6]
        )
        techniques_text = "\n".join(
            f"  - [{t['confidence']:.0%}] {t['label']}: {t['description']}"
            for t in curiosity_outputs.get("technique_candidates", [])[:6]
        )
        summary = curiosity_outputs.get("data_summary", {})
        shape = summary.get("shape", {})
        spec = f"""Generate an analysis map grounded in real data.
Goal: {goal}
Why it matters: {why}
Dataset: {shape.get('rows', '?')} rows × {shape.get('cols', '?')} columns

Data-driven questions the AI identified (use the most important as question nodes):
{questions_text}

Data-driven technique candidates (use the most relevant as technique nodes):
{techniques_text}

Include:
- 1 goal node (id: "goal-1") capturing the core objective
- 1-2 data_source nodes (ids: "ds-1", ...) representing the uploaded dataset
- 2-3 technique nodes (ids: "tech-1", ...) from the technique candidates above
- 2-3 question nodes (ids: "q-1", ...) from the most important questions above
Connect each data_source and technique to "goal-1", and "goal-1" to each question."""
    else:
        spec = f"""Generate an analysis map for:
Goal: {goal}
Why it matters: {why}
Available data: {available_data}
Ideas/techniques: {ideas}

Include:
- 1 goal node (id: "goal-1") capturing the core objective
- 2-3 data_source nodes (ids: "ds-1", "ds-2", ...) from the described datasets
- 1-2 question nodes (ids: "q-1", "q-2") with the most important clarifying questions
Connect each data_source to "goal-1", and "goal-1" to each question."""

    response = _get_client().models.generate_content(model=_MODEL, contents=_map_prompt(spec))
    return _parse_json_nodes(response.text)


def generate_research_nodes(
    nodes: list[Node],
    goal: str,
    curiosity_outputs: dict | None = None,
    iteration: int = 1,
) -> tuple[list[Node], list[Edge]]:
    existing_labels = {n.data.label for n in nodes}
    existing = "\n".join(f"  - {n.data.type}: {n.data.label}" for n in nodes)

    if curiosity_outputs:
        # Filter out candidates already represented in the map
        remaining_q = [
            q for q in curiosity_outputs.get("question_candidates", [])
            if not any(q["label"].lower() in label.lower() or label.lower() in q["label"].lower()
                       for label in existing_labels)
        ][:4]
        remaining_t = [
            t for t in curiosity_outputs.get("technique_candidates", [])
            if not any(t["label"].lower() in label.lower() or label.lower() in t["label"].lower()
                       for label in existing_labels)
        ][:4]

        if not remaining_q and not remaining_t:
            return [], []

        questions_text = "\n".join(
            f"  - {q['label']}: {q['description']}" for q in remaining_q
        )
        techniques_text = "\n".join(
            f"  - {t['label']}: {t['description']}" for t in remaining_t
        )
        spec = f"""Expand this analysis map (research iteration {iteration}).
Goal: {goal}

Current map nodes:
{existing}

New data-driven questions not yet covered (add the most important as question nodes):
{questions_text or '(none remaining)'}

New technique suggestions not yet covered (add the most relevant as technique nodes):
{techniques_text or '(none remaining)'}

Add only nodes that are NOT already in the current map.
If nothing meaningful to add, return an empty nodes array.
Use ids like "r{iteration}-q1", "r{iteration}-t1". Connect all to "goal-1"."""
    else:
        spec = f"""Expand this analysis map.
Goal: {goal}
Current nodes:
{existing}

Add:
- 1-2 technique nodes (ids: "tech-{iteration}-1", ...) — specific analysis methods
- 1 question node (id: "q-r{iteration}") — one more clarifying question
Connect all to "goal-1"."""

    response = _get_client().models.generate_content(model=_MODEL, contents=_map_prompt(spec))
    return _parse_json_nodes(response.text)


def process_feedback(node: Node, all_nodes: list[Node], feedback: str, deeper: bool) -> tuple[list[Node], list[Edge]]:
    goal = next((n.data.label for n in all_nodes if n.data.type == "goal"), "")
    mode = "Return 2-3 new technique/question nodes." if deeper else "Return 1 updated or replacement node."
    spec = f"""Update the analysis map based on feedback.
Goal: {goal}
Selected node: {node.data.type} "{node.data.label}" (id: {node.id})
Feedback: {feedback}
{mode} Use ids like "fb-1", "fb-2". Connect to "goal-1"."""

    response = _get_client().models.generate_content(model=_MODEL, contents=_map_prompt(spec))
    return _parse_json_nodes(response.text)


async def select_modules(foundation_summary: dict, goal: str) -> list[str]:
    from analysis.modules import build_selection_prompt
    prompt = build_selection_prompt(foundation_summary, goal)
    response = await _get_client().aio.models.generate_content(model=_MODEL, contents=prompt)
    text = response.text.strip()
    match = re.search(r"\[[\s\S]*?\]", text)
    if match:
        try:
            modules = json.loads(match.group())
            valid = {"exploratory", "time_series", "ranking", "business", "text", "anomaly"}
            return [m for m in modules if m in valid][:4]
        except json.JSONDecodeError:
            pass
    return ["exploratory"]


async def stream_synthesis(ctx) -> AsyncGenerator[dict, None]:
    synthesis_input = ctx.to_gemini_synthesis_input()

    findings_text = "\n".join(
        f"\n[{script}]\n" + "\n".join(f"  - {f}" for f in findings)
        for script, findings in synthesis_input["script_findings"].items()
    )

    prompt = f"""You are a senior data analyst presenting findings to a business stakeholder.

User goal: {synthesis_input['goal']}
Dataset: {synthesis_input['shape']['rows']:,} rows × {synthesis_input['shape']['cols']} columns
Modules run: {', '.join(synthesis_input['active_modules'])}

Deterministic analysis findings:
{findings_text}

Your task:
1. Walk through the most important findings step by step, explaining them in plain English.
2. After each major insight, output a finding marker on its own line in this exact format:
   FINDING: <label> | <1-2 sentence description> | <confidence 0.0-1.0>
3. Connect findings across scripts when they corroborate each other.
4. Focus on what directly answers the user's goal.
5. End with: COMPLETE: <2-sentence executive summary>"""

    finding_index = 0
    buffer = ""

    async for chunk in await _get_client().aio.models.generate_content_stream(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=2000),
    ):
        text = chunk.text if chunk.text else ""
        buffer += text

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue

            if line.startswith("FINDING:"):
                parts = line[len("FINDING:"):].strip().split("|")
                if len(parts) >= 2:
                    label = parts[0].strip()
                    description = parts[1].strip()
                    confidence = float(parts[2].strip()) if len(parts) > 2 else 0.8
                    fid = f"finding-{finding_index}"
                    finding_index += 1
                    node = {
                        "id": fid, "type": "findingNode",
                        "position": {"x": 780, "y": 120 + finding_index * 190},
                        "data": {
                            "label": label, "description": description,
                            "type": "finding", "status": "complete",
                            "metadata": {"confidence": min(max(confidence, 0), 1)},
                        },
                    }
                    edge = {"id": f"e-goal-{fid}", "source": "goal-1",
                            "target": fid, "animated": True}
                    yield {"event": "node_add",
                           "data": json.dumps({"node": node, "edge": edge})}

            elif line.startswith("COMPLETE:"):
                summary = line[len("COMPLETE:"):].strip()
                yield {"event": "complete",
                       "data": json.dumps({"summary": summary})}
                return

            else:
                yield {"event": "log", "data": json.dumps({"message": line})}

    if buffer.strip():
        yield {"event": "log", "data": json.dumps({"message": buffer.strip()})}

    yield {"event": "complete",
           "data": json.dumps({"summary": f"Analysis complete. Found {finding_index} insights."})}
