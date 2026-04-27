from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import AsyncGenerator

from openai import OpenAI, AsyncOpenAI

from schemas.models import Node, Edge, NodeData, NodePosition

_MODEL = "openai/gpt-4o-mini"
_BASE_URL = "https://models.github.ai/inference"
_client: OpenAI | None = None
_async_client: AsyncOpenAI | None = None

# Load analytical frameworks library once at module startup
_FRAMEWORKS_PATH = Path(__file__).parent.parent / "data" / "frameworks.json"
try:
    _FRAMEWORKS: list[dict] = json.loads(_FRAMEWORKS_PATH.read_text(encoding="utf-8"))
except Exception:
    _FRAMEWORKS = []


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


def _call(prompt: str, temperature: float = 0.7) -> str:
    response = _get_client().chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return _strip_think(response.choices[0].message.content or "")


def _match_frameworks(goal: str, available_data: str, column_names: list[str]) -> list[dict]:
    """Score frameworks by keyword overlap with goal/data. Return top 3."""
    if not _FRAMEWORKS:
        return []

    combined_text = (goal + " " + available_data + " " + " ".join(column_names)).lower()

    def score(fw: dict) -> float:
        kw_hits = sum(1 for kw in fw.get("required_keywords", []) if kw in combined_text)
        domain_hits = sum(1 for d in fw.get("domain", []) if d in combined_text)
        return kw_hits * 2 + domain_hits

    scored = [(score(fw), fw) for fw in _FRAMEWORKS]
    scored.sort(key=lambda x: -x[0])
    return [fw for s, fw in scored[:3] if s > 0]


def _brainstorm(goal: str, why: str, data_context: str, sampled_rows: list[dict] | None = None) -> str:
    rows_text = ""
    if sampled_rows:
        rows_lines = "\n".join(
            f"  {i+1}. {json.dumps(row, default=str)}"
            for i, row in enumerate(sampled_rows[:8])
        )
        rows_text = f"\nSample data records (diverse rows from the actual CSV):\n{rows_lines}"

    prompt = f"""You are a curious, unconventional data analyst. Before building an analysis map, brainstorm investigative angles.

Goal: {goal}
Why it matters: {why}
Data context: {data_context}{rows_text}

Generate exactly 10 distinct investigative paths or hypotheses to explore.
Go beyond the obvious — include surprising angles, counter-intuitive questions, hidden drivers, edge cases, and non-linear relationships.
Reference specific column names and actual data values where possible.
Each item should suggest a concrete thing to measure or test.

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
             data=NodeData(label="Trend Analysis", description="Identify time-based patterns in revenue column.", type="technique", status="active")),
        Node(id="tech-2", type="techniqueNode", position=NodePosition(x=380, y=280),
             data=NodeData(label="Segment Comparison", description="Compare performance across product_category column.", type="technique", status="active")),
        Node(id="q-1", type="questionNode", position=NodePosition(x=880, y=80),
             data=NodeData(label="Which segments drive growth?", description="Are certain product_category values accelerating while others stagnate?", type="question", status="active")),
        Node(id="q-2", type="questionNode", position=NodePosition(x=880, y=280),
             data=NodeData(label="Is growth seasonal?", description="Do revenue peaks in the date column correlate with calendar events?", type="question", status="active")),
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
             data=NodeData(label=f"Mock Technique R{iteration}", description=f"Research wave {iteration} technique referencing revenue column.", type="technique", status="active")),
        Node(id=f"r{iteration}-q1", type="questionNode",
             position=NodePosition(x=880, y=y_offset),
             data=NodeData(label=f"Mock Question R{iteration}", description=f"Research wave {iteration} question about date column patterns.", type="question", status="active")),
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
    return NodePosition(x=bx, y=80 + index * 240)


def _parse_json_nodes(
    text: str,
    type_offset: dict[str, int] | None = None,
    known_columns: set[str] | None = None,
) -> tuple[list[Node], list[Edge]]:
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

        status = n.get("status", "active")
        # Column grounding: flag question nodes whose description doesn't cite a known column
        if nt == "question" and known_columns:
            desc_lower = n.get("description", "").lower()
            if not any(col.lower() in desc_lower for col in known_columns):
                status = "low_confidence"

        nodes.append(Node(
            id=n["id"],
            type=REACT_TYPE_MAP.get(nt, "custom"),
            position=_position(nt, idx),
            data=NodeData(
                label=n["label"],
                description=n["description"],
                type=nt,  # type: ignore[arg-type]
                status=status,  # type: ignore[arg-type]
                metadata=n.get("metadata"),
            ),
        ))
    edges = [
        Edge(id=e["id"], source=e["source"], target=e["target"], animated=True)
        for e in raw.get("edges", [])
    ]
    return nodes, edges


def _map_prompt(nodes_spec: str, column_list: str = "") -> str:
    grounding_rule = ""
    if column_list:
        grounding_rule = f"""
COLUMN GROUNDING (MANDATORY):
- Available columns in this dataset: {column_list}
- Every question node description MUST reference at least one exact column name from the list above.
- Example: "Does the revenue column show seasonality correlated with the date column?"
- If you cannot reference a specific column, do NOT include the question node.
"""
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
{grounding_rule}
CHAINING RULES:
- Any node can connect to any other node — not just goal-1
- Build deep chains: data_source → technique → question
- Edges show reasoning flow and dependencies between ideas
- A technique can lead to multiple questions

{nodes_spec}"""


def _critic_pass(nodes: list[Node], column_names: list[str]) -> list[Node]:
    """LLM critic pass: flag nodes that can't be answered from the given columns."""
    if not nodes or not column_names:
        return nodes

    compact = [
        {"id": n.id, "type": n.data.type, "label": n.data.label, "description": n.data.description}
        for n in nodes
        if n.data.type in ("question", "technique")
    ]
    if not compact:
        return nodes

    col_list = ", ".join(column_names)
    prompt = f"""You are a skeptical senior data scientist reviewing proposed analysis nodes.
Dataset columns available: {col_list}

For each node below, decide if it can be answered/executed using ONLY those columns.
Return ONLY a JSON array — no explanation outside the array.

Rules for keep=false:
- Question cannot be answered with the available columns
- Question is too generic (e.g. "What are the main trends?" with no column cited)
- Node is a near-duplicate of another node in the list

Format: [{{"id": "...", "keep": true, "reason": "..."}}]

Nodes to evaluate:
{json.dumps(compact, indent=2)}"""

    try:
        result = _call(prompt, temperature=0.2)
        match = re.search(r"\[[\s\S]*?\]", result)
        if not match:
            return nodes
        verdicts: list[dict] = json.loads(match.group())
        verdict_map = {v["id"]: v for v in verdicts if isinstance(v, dict)}
        updated = []
        for n in nodes:
            v = verdict_map.get(n.id)
            if v and not v.get("keep", True):
                meta = dict(n.data.metadata or {})
                meta["critic_reason"] = v.get("reason", "Flagged by critic")
                updated.append(Node(
                    id=n.id, type=n.type, position=n.position,
                    data=NodeData(
                        label=n.data.label, description=n.data.description,
                        type=n.data.type,  # type: ignore[arg-type]
                        status="low_confidence",  # type: ignore[arg-type]
                        metadata=meta,
                    ),
                ))
            else:
                updated.append(n)
        return updated
    except Exception:
        return nodes


def generate_initial_map(
    goal: str,
    why: str,
    available_data: str,
    ideas: str,
    curiosity_outputs: dict | None = None,
) -> tuple[list[Node], list[Edge]]:
    if _MOCK_MODE:
        return _mock_initial_map()

    # Extract column names and sampled rows from curiosity outputs
    column_names: list[str] = []
    sampled_rows: list[dict] = []
    if curiosity_outputs:
        col_map = curiosity_outputs.get("data_summary", {}).get("columns", {})
        column_names = list(col_map.keys())
        sampled_rows = curiosity_outputs.get("sampled_rows", [])

    # Match expert frameworks by keyword overlap
    matched_frameworks = _match_frameworks(goal, available_data, column_names)
    frameworks_text = ""
    if matched_frameworks:
        fw_lines = []
        for fw in matched_frameworks:
            fw_lines.append(f"  [{fw['name']}]")
            for q in fw.get("questions", [])[:2]:
                fw_lines.append(f"    Q: {q}")
            for t in fw.get("techniques", [])[:2]:
                fw_lines.append(f"    T: {t}")
        frameworks_text = "\nRelevant expert frameworks to draw from:\n" + "\n".join(fw_lines)

    # brainstorm first — forces LLM to explore non-obvious angles
    data_context = available_data or ("CSV dataset" if curiosity_outputs else ideas)
    brainstorm = _brainstorm(goal, why, data_context, sampled_rows=sampled_rows)

    column_list = ", ".join(column_names) if column_names else ""
    known_columns = set(column_names) if column_names else None

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
Columns: {column_list}
{frameworks_text}
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
- 2-3 question nodes (ids: "q-1", ...) — must reference specific column names
Build chains — techniques connect to questions. Go deep."""
    else:
        spec = f"""Generate an analysis map.
Goal: {goal}
Why it matters: {why}
Available data: {available_data}
Ideas/techniques: {ideas}
{frameworks_text}
Brainstormed investigative angles (pick the most powerful, non-obvious ones):
{brainstorm}

Include:
- 1 goal node (id: "goal-1")
- 1-2 data_source nodes (ids: "ds-1", "ds-2", ...)
- 2-3 technique nodes (ids: "tech-1", ...) — prioritise non-obvious angles from brainstorm
- 2-3 question nodes (ids: "q-1", "q-2", ...) — prioritise surprising questions
Build chains — any node can connect to any other. Go deep."""

    nodes, edges = _parse_json_nodes(_call(_map_prompt(spec, column_list)), known_columns=known_columns)

    # Critic pass: flag nodes that can't be answered from the given columns
    if column_names and nodes:
        nodes = _critic_pass(nodes, column_names)

    return nodes, edges


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

    column_names: list[str] = []
    if curiosity_outputs:
        col_map = curiosity_outputs.get("data_summary", {}).get("columns", {})
        column_names = list(col_map.keys())

    column_list = ", ".join(column_names) if column_names else ""
    known_columns = set(column_names) if column_names else None

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
Build chains: technique → question. Any node can connect to any other."""
    else:
        has_more = True
        spec = f"""Expand this analysis map (iteration {iteration}).
Goal: {goal}

Current nodes:
{existing}

Add 2-4 new nodes that deepen the analysis:
- technique nodes (ids: "tech-{iteration}-1", ...) — specific analysis methods
- question nodes (ids: "q-{iteration}-1", ...) — clarifying or probing questions

IMPORTANT: Connect nodes to each other meaningfully — not just to goal-1.
Existing node ids are listed above — reference them in edges.
If you have nothing meaningful to add, return an empty nodes array."""

    result_nodes, result_edges = _parse_json_nodes(
        _call(_map_prompt(spec, column_list)), type_offset, known_columns
    )
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
    from analysis.modules import build_selection_prompt, MODULE_COMPUTE_COSTS
    prompt = build_selection_prompt(foundation_summary, goal)
    text = await _acall(prompt)
    match = re.search(r"\[[\s\S]*?\]", text)
    if not match:
        return ["exploratory"]
    try:
        modules = json.loads(match.group())
        valid = set(MODULE_COMPUTE_COSTS.keys())
        selected = [m for m in modules if m in valid]

        # Enforce budget: drop lowest-cost modules until within 6-point budget
        total_cost = sum(MODULE_COMPUTE_COSTS.get(m, 1) for m in selected)
        while total_cost > 6 and selected:
            # Drop the last module (lowest priority)
            dropped = selected.pop()
            total_cost -= MODULE_COMPUTE_COSTS.get(dropped, 1)

        return selected or ["exploratory"]
    except json.JSONDecodeError:
        return ["exploratory"]


def generate_quick_insights(ctx) -> list[tuple[dict, dict]]:
    """Generate 2-3 immediate statistical findings from Phase 1 foundation data.
    Returns list of (node_dict, edge_dict) tuples ready for SSE emission."""
    if _MOCK_MODE:
        return []

    summary = ctx.to_gemini_summary()
    shape = summary.get("shape", {})

    # Build a compact data profile for the prompt
    profile_lines = []
    for col_name, col_info in list(summary.get("columns", {}).items())[:8]:
        inferred = col_info.get("inferred_type", "")
        samples = col_info.get("sample_values", [])[:3]
        profile_lines.append(f"  {col_name} ({inferred}): samples={samples}")

    quality = summary.get("quality", {})
    null_rate = quality.get("overall_null_rate", 0)
    dup_rate = quality.get("duplicate_rate", 0)

    prompt = f"""You are a data analyst. Based only on this dataset profile, identify 2-3 immediate statistical observations.
Each observation MUST cite a specific number, percentage, or column name.
Do NOT speculate — only report what the numbers directly show.

Dataset: {shape.get('rows', 0):,} rows × {shape.get('cols', 0)} columns
Null rate: {null_rate:.1%} | Duplicate rate: {dup_rate:.1%}
Columns:
{chr(10).join(profile_lines)}

For each observation, output one line in this exact format:
QUICK: <short label> | <1-sentence description with a specific number> | <confidence 0.0-1.0>

Example:
QUICK: High Null Rate | The overall_null_rate column has 23.4% missing values, reducing usable rows to approximately 7,660. | 0.95

Output 2-3 QUICK lines only. No other text."""

    try:
        text = _call(prompt, temperature=0.3)
        results = []
        qf_index = 0
        for line in text.split("\n"):
            line = line.strip()
            if not line.startswith("QUICK:"):
                continue
            parts = re.split(r"\s*\|\s*", line[len("QUICK:"):].strip(), maxsplit=2)
            if len(parts) < 2:
                continue
            label = parts[0].strip()
            description = parts[1].strip()
            try:
                confidence = float(parts[2].strip()) if len(parts) > 2 else 0.9
            except ValueError:
                confidence = 0.9

            fid = f"qf-{qf_index}"
            qf_index += 1
            node_dict = {
                "id": fid,
                "type": "findingNode",
                "position": {"x": 1280, "y": 80 + qf_index * 200},
                "data": {
                    "label": label,
                    "description": description,
                    "type": "finding",
                    "status": "complete",
                    "metadata": {"confidence": min(max(confidence, 0), 1), "source": "quick_insight"},
                },
            }
            edge_dict = {
                "id": f"e-goal-{fid}",
                "source": "goal-1",
                "target": fid,
                "animated": True,
            }
            results.append((node_dict, edge_dict))
            if qf_index >= 3:
                break
        return results
    except Exception:
        return []


async def stream_synthesis(ctx) -> AsyncGenerator[dict, None]:
    synthesis_input = ctx.to_gemini_synthesis_input()

    findings_text = "\n".join(
        f"\n[{script}]\n" + "\n".join(f"  - {f}" for f in findings)
        for script, findings in synthesis_input["script_findings"].items()
    )

    prompt = f"""You are a senior data analyst synthesising findings for a business stakeholder.

User goal: {synthesis_input['goal']}
Dataset: {synthesis_input['shape']['rows']:,} rows × {synthesis_input['shape']['cols']} columns
Modules run: {', '.join(synthesis_input['active_modules'])}

Deterministic analysis findings:
{findings_text}

Your task:
1. Walk through the most important findings in plain English. Be concise.
2. CHAIN OF DENSITY: Each finding must cite at least one specific number, percentage, or column name.
   Merge redundant findings into single, richer ones. Do not repeat the same finding twice.
3. After each major insight, output a finding marker on its own line:
   FINDING: <short label> | <1-2 sentence data-dense description> | <confidence 0.0-1.0>
4. CONFIDENCE JUSTIFICATION: Before each confidence score, write a 1-sentence mathematical basis
   inside the description (e.g. "…r=0.78 with n=5,000 rows, confidence 0.92").
5. Connect findings when they corroborate each other.
6. Focus on what directly answers the user's goal.
7. End with: COMPLETE: <2-sentence executive summary with key numbers>"""

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
        if not chunk.choices:
            continue
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
                parts = re.split(r"\s*\|\s*", line[len("FINDING:"):].strip(), maxsplit=2)
                if len(parts) >= 2:
                    label = parts[0].strip()
                    description = parts[1].strip()
                    try:
                        confidence = float(parts[2].strip()) if len(parts) > 2 else 0.8
                    except ValueError:
                        confidence = 0.8
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
