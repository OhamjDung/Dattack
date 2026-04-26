from __future__ import annotations
import json
import os
import re
from typing import AsyncGenerator

from openai import OpenAI, AsyncOpenAI

from schemas.models import Node, Edge, NodeData, NodePosition

_MODEL = "deepseek/DeepSeek-R1-0528"
_BASE_URL = "https://models.github.ai/inference"
_client: OpenAI | None = None
_async_client: AsyncOpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            raise RuntimeError("GITHUB_TOKEN is not set")
        _client = OpenAI(base_url=_BASE_URL, api_key=token)
    return _client


def _get_async_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            raise RuntimeError("GITHUB_TOKEN is not set")
        _async_client = AsyncOpenAI(base_url=_BASE_URL, api_key=token)
    return _async_client


def _strip_think(text: str) -> str:
    return re.sub(r"<think>[\s\S]*?</think>", "", text).strip()


_MOCK_MODE = os.environ.get("MOCK_MODE", "").lower() in ("1", "true", "yes")


def _call(prompt: str) -> str:
    response = _get_client().chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return _strip_think(response.choices[0].message.content or "")


def _brainstorm(goal: str, why: str, data_context: str) -> str:
    prompt = f"""You are a curious, unconventional data analyst. Before building an analysis map, brainstorm investigative angles.

Goal: {goal}
Why it matters: {why}
Data context: {data_context}

Generate exactly 10 distinct investigative paths or hypotheses to explore.
Go beyond the obvious — include surprising angles, counter-intuitive questions, hidden drivers, edge cases, and non-linear relationships.
Be specific. Each item should suggest a concrete thing to measure or test.

Format: numbered list 1-10, one per line. No preamble, no conclusion."""
    return _call(prompt)


def _mock_initial_map() -> tuple[list[Node], list[Edge]]:
    nodes = [
        Node(id="goal-1", type="goalNode", position=NodePosition(x=580, y=400),
             data=NodeData(label="Mock Goal", description="This is mock data. Set MOCK_MODE= to use real LLM.", type="goal", status="active")),
        Node(id="ds-1", type="dataSourceNode", position=NodePosition(x=80, y=80),
             data=NodeData(label="Sales Dataset", description="Mock CSV with 1,200 rows and 8 columns.", type="data_source", status="active")),
        Node(id="ds-2", type="dataSourceNode", position=NodePosition(x=80, y=280),
             data=NodeData(label="Customer Data", description="Mock customer demographics, 4 columns.", type="data_source", status="active")),
        Node(id="tech-1", type="techniqueNode", position=NodePosition(x=380, y=80),
             data=NodeData(label="Trend Analysis", description="Identify time-based patterns in revenue.", type="technique", status="active")),
        Node(id="tech-2", type="techniqueNode", position=NodePosition(x=380, y=280),
             data=NodeData(label="Segment Comparison", description="Compare performance across product categories.", type="technique", status="active")),
        Node(id="q-1", type="questionNode", position=NodePosition(x=880, y=80),
             data=NodeData(label="Which segments drive growth?", description="Are certain categories accelerating while others stagnate?", type="question", status="active")),
        Node(id="q-2", type="questionNode", position=NodePosition(x=880, y=280),
             data=NodeData(label="Is growth seasonal?", description="Do peaks correlate with calendar events or promotions?", type="question", status="active")),
    ]
    edges = [
        Edge(id="e-ds1-goal1", source="ds-1", target="goal-1", animated=True),
        Edge(id="e-ds2-goal1", source="ds-2", target="goal-1", animated=True),
        Edge(id="e-goal1-tech1", source="goal-1", target="tech-1", animated=True),
        Edge(id="e-goal1-tech2", source="goal-1", target="tech-2", animated=True),
        Edge(id="e-tech1-q1", source="tech-1", target="q-1", animated=True),
        Edge(id="e-tech2-q2", source="tech-2", target="q-2", animated=True),
    ]
    return nodes, edges


def _mock_research_nodes(iteration: int) -> tuple[list[Node], list[Edge], bool]:
    if iteration > 2:
        return [], [], False
    y_offset = 480 + (iteration - 1) * 220
    nodes = [
        Node(id=f"r{iteration}-t1", type="techniqueNode",
             position=NodePosition(x=380, y=y_offset),
             data=NodeData(label=f"Mock Technique R{iteration}", description=f"Research wave {iteration} technique.", type="technique", status="active")),
        Node(id=f"r{iteration}-q1", type="questionNode",
             position=NodePosition(x=880, y=y_offset),
             data=NodeData(label=f"Mock Question R{iteration}", description=f"Research wave {iteration} question.", type="question", status="active")),
    ]
    edges = [
        Edge(id=f"e-goal1-r{iteration}-t1", source="goal-1", target=f"r{iteration}-t1", animated=True),
        Edge(id=f"e-r{iteration}-t1-r{iteration}-q1", source=f"r{iteration}-t1", target=f"r{iteration}-q1", animated=True),
    ]
    return nodes, edges, iteration < 2


async def _acall(prompt: str) -> str:
    response = await _get_async_client().chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return _strip_think(response.choices[0].message.content or "")


REACT_TYPE_MAP = {
    "goal": "goalNode",
    "data_source": "dataSourceNode",
    "technique": "techniqueNode",
    "question": "questionNode",
    "finding": "findingNode",
    "insight": "insightNode",
}

_LAYOUT: dict[str, tuple[int, int]] = {
    "goal":        (580, 400),
    "data_source": (80,  80),
    "technique":   (380, 80),
    "question":    (880, 80),
    "finding":     (1280, 80),
    "insight":     (1280, 80),
}


def _position(node_type: str, index: int) -> NodePosition:
    bx, _ = _LAYOUT.get(node_type, (400, 0))
    if node_type == "goal":
        return NodePosition(x=bx, y=300)
    return NodePosition(x=bx, y=80 + index * 200)


def _parse_json_nodes(text: str, type_offset: dict[str, int] | None = None) -> tuple[list[Node], list[Edge]]:
    if type_offset is None:
        type_offset = {}
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return [], []
    raw = json.loads(match.group())
    type_counts: dict[str, int] = {}
    nodes: list[Node] = []
    for n in raw.get("nodes", []):
        nt: str = n.get("node_type", "technique")
        if nt not in REACT_TYPE_MAP:
            nt = "technique"
        local_idx = type_counts.get(nt, 0)
        type_counts[nt] = local_idx + 1
        idx = local_idx + type_offset.get(nt, 0)
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
    return f"""Return ONLY a valid JSON object. No markdown, no explanation, no <think> tags. Just raw JSON.

Structure:
{{
  "nodes": [
    {{"id": "goal-1", "node_type": "goal", "label": "...", "description": "...", "status": "active"}},
    {{"id": "ds-1", "node_type": "data_source", "label": "...", "description": "...", "status": "active"}}
  ],
  "edges": [
    {{"id": "e-ds1-goal1", "source": "ds-1", "target": "goal-1"}}
  ]
}}

node_type must be exactly one of: goal, data_source, technique, question, finding

CHAINING RULES:
- Any node can connect to any other node — not just goal-1
- Build deep chains: data_source → technique → question → insight
- Edges show reasoning flow and dependencies between ideas
- A technique can lead to multiple questions; a question can spawn insights

{nodes_spec}"""


def generate_initial_map(
    goal: str,
    why: str,
    available_data: str,
    ideas: str,
    curiosity_outputs: dict | None = None,
) -> tuple[list[Node], list[Edge]]:
    if _MOCK_MODE:
        return _mock_initial_map()

    # brainstorm first — forces LLM to explore non-obvious angles before committing to a map
    data_context = available_data or (f"CSV dataset" if curiosity_outputs else ideas)
    brainstorm = _brainstorm(goal, why, data_context)

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

Brainstormed investigative angles (pick the most powerful, non-obvious ones):
{brainstorm}

Data-driven questions identified:
{questions_text}

Data-driven technique candidates:
{techniques_text}

Include:
- 1 goal node (id: "goal-1")
- 1-2 data_source nodes (ids: "ds-1", ...)
- 2-3 technique nodes (ids: "tech-1", ...) — prioritise non-obvious angles from brainstorm
- 2-3 question nodes (ids: "q-1", ...) — prioritise surprising or counter-intuitive questions
Build chains — techniques connect to questions, questions connect to each other. Go deep."""
    else:
        spec = f"""Generate an analysis map.
Goal: {goal}
Why it matters: {why}
Available data: {available_data}
Ideas/techniques: {ideas}

Brainstormed investigative angles (pick the most powerful, non-obvious ones):
{brainstorm}

Include:
- 1 goal node (id: "goal-1")
- 1-2 data_source nodes (ids: "ds-1", "ds-2", ...)
- 2-3 technique nodes (ids: "tech-1", ...) — prioritise non-obvious angles from brainstorm
- 2-3 question nodes (ids: "q-1", "q-2", ...) — prioritise surprising questions
Build chains — any node can connect to any other. Go deep."""

    return _parse_json_nodes(_call(_map_prompt(spec)))


def generate_research_nodes(
    nodes: list[Node],
    goal: str,
    curiosity_outputs: dict | None = None,
    iteration: int = 1,
) -> tuple[list[Node], list[Edge], bool]:
    if _MOCK_MODE:
        return _mock_research_nodes(iteration)

    existing_labels = {n.data.label for n in nodes}
    existing = "\n".join(f"  - {n.data.type}: {n.data.label} (id: {n.id})" for n in nodes)

    # compute type offsets so new nodes don't overlap existing ones
    type_offset: dict[str, int] = {}
    for n in nodes:
        nt = n.data.type
        type_offset[nt] = type_offset.get(nt, 0) + 1

    if curiosity_outputs:
        all_remaining_q = [
            q for q in curiosity_outputs.get("question_candidates", [])
            if not any(q["label"].lower() in label.lower() or label.lower() in q["label"].lower()
                       for label in existing_labels)
        ]
        all_remaining_t = [
            t for t in curiosity_outputs.get("technique_candidates", [])
            if not any(t["label"].lower() in label.lower() or label.lower() in t["label"].lower()
                       for label in existing_labels)
        ]

        remaining_q = all_remaining_q[:4]
        remaining_t = all_remaining_t[:4]
        has_more = len(all_remaining_q) > 4 or len(all_remaining_t) > 4

        if not remaining_q and not remaining_t:
            return [], [], False

        questions_text = "\n".join(f"  - {q['label']}: {q['description']}" for q in remaining_q)
        techniques_text = "\n".join(f"  - {t['label']}: {t['description']}" for t in remaining_t)
        spec = f"""Expand this analysis map (research iteration {iteration}).
Goal: {goal}

Current map nodes:
{existing}

New questions not yet covered — add the most important as question nodes:
{questions_text or '(none remaining)'}

New technique suggestions not yet covered — add the most relevant as technique nodes:
{techniques_text or '(none remaining)'}

Add only nodes NOT already in the map. If nothing meaningful, return empty nodes array.
Use ids like "r{iteration}-q1", "r{iteration}-t1".
IMPORTANT: Connect nodes to each other meaningfully — not just to goal-1.
Build chains: technique → question → insight. Any node can connect to any other."""
    else:
        has_more = True  # without curiosity data, let early termination decide
        spec = f"""Expand this analysis map (iteration {iteration}).
Goal: {goal}

Current nodes:
{existing}

Add 2-4 new nodes that deepen the analysis:
- technique nodes (ids: "tech-{iteration}-1", ...) — specific analysis methods
- question nodes (ids: "q-{iteration}-1", ...) — clarifying or probing questions
- insight nodes (ids: "ins-{iteration}-1", ...) — hypotheses or expected patterns

IMPORTANT: Connect nodes to each other meaningfully — not just to goal-1.
Existing node ids are listed above — reference them in edges.
If you have nothing meaningful to add, return an empty nodes array."""

    result_nodes, result_edges = _parse_json_nodes(_call(_map_prompt(spec)), type_offset)
    if not result_nodes:
        has_more = False
    return result_nodes, result_edges, has_more


def process_feedback(node: Node, all_nodes: list[Node], feedback: str, deeper: bool) -> tuple[list[Node], list[Edge]]:
    goal = next((n.data.label for n in all_nodes if n.data.type == "goal"), "")
    existing = "\n".join(f"  - {n.data.type}: {n.data.label} (id: {n.id})" for n in all_nodes)
    type_offset: dict[str, int] = {}
    for n in all_nodes:
        nt = n.data.type
        type_offset[nt] = type_offset.get(nt, 0) + 1

    if deeper:
        mode = "Return 2-4 new nodes exploring this direction deeply. Use node_type 'insight' for user-feedback-driven ideas."
    else:
        mode = "Return 1-2 updated or replacement nodes. Use node_type 'insight' for user-driven ideas."

    spec = f"""Update the analysis map based on user feedback.
Goal: {goal}
Selected node: {node.data.type} "{node.data.label}" (id: {node.id})
Feedback: {feedback}

Current map nodes:
{existing}

{mode}
Use ids like "fb-1", "fb-2". Connect to relevant existing nodes — not just goal-1.
Build chains from the feedback direction."""

    result_nodes, result_edges = _parse_json_nodes(_call(_map_prompt(spec)), type_offset)
    return result_nodes, result_edges


async def select_modules(foundation_summary: dict, goal: str) -> list[str]:
    from analysis.modules import build_selection_prompt
    prompt = build_selection_prompt(foundation_summary, goal)
    text = await _acall(prompt)
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

    stream = await _get_async_client().chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        max_tokens=2000,
        temperature=0.7,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        buffer += delta

        # strip think tags spanning chunks
        buffer = re.sub(r"<think>[\s\S]*?</think>", "", buffer)

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
