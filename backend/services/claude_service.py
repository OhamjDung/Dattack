import anthropic
from schemas.models import Node, Edge, NodeData, NodePosition

client = anthropic.Anthropic()

REACT_TYPE_MAP = {
    "goal": "goalNode",
    "data_source": "dataSourceNode",
    "technique": "techniqueNode",
    "question": "questionNode",
    "finding": "findingNode",
}

_LAYOUT_BASE: dict[str, tuple[int, int]] = {
    "goal": (450, 300),
    "data_source": (100, 0),
    "technique": (450, 0),
    "question": (780, 0),
    "finding": (780, 0),
}


def _position(node_type: str, index: int) -> NodePosition:
    bx, _ = _LAYOUT_BASE.get(node_type, (300, 0))
    if node_type == "goal":
        return NodePosition(x=bx, y=300)
    return NodePosition(x=bx, y=120 + index * 190)


OUTPUT_MAP_TOOL: dict = {
    "name": "output_map",
    "description": "Output nodes and edges for the analysis map",
    "input_schema": {
        "type": "object",
        "properties": {
            "nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "node_type": {
                            "type": "string",
                            "enum": ["goal", "data_source", "technique", "question"],
                        },
                        "label": {"type": "string"},
                        "description": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "active", "answered", "complete"],
                        },
                        "metadata": {"type": "object"},
                    },
                    "required": ["id", "node_type", "label", "description"],
                },
            },
            "edges": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "source": {"type": "string"},
                        "target": {"type": "string"},
                    },
                    "required": ["id", "source", "target"],
                },
            },
        },
        "required": ["nodes", "edges"],
    },
}


def _parse_tool_result(result: dict) -> tuple[list[Node], list[Edge]]:
    type_counts: dict[str, int] = {}
    nodes: list[Node] = []
    for n in result.get("nodes", []):
        nt: str = n["node_type"]
        idx = type_counts.get(nt, 0)
        type_counts[nt] = idx + 1
        nodes.append(
            Node(
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
            )
        )
    edges = [
        Edge(id=e["id"], source=e["source"], target=e["target"], animated=True)
        for e in result.get("edges", [])
    ]
    return nodes, edges


def _tool_call(prompt: str, max_tokens: int = 1500) -> tuple[list[Node], list[Edge]]:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        tools=[OUTPUT_MAP_TOOL],
        tool_choice={"type": "tool", "name": "output_map"},
        messages=[{"role": "user", "content": prompt}],
    )
    tool_use = next(b for b in response.content if b.type == "tool_use")
    return _parse_tool_result(tool_use.input)  # type: ignore[arg-type]


def generate_initial_map(goal: str, why: str, available_data: str, ideas: str) -> tuple[list[Node], list[Edge]]:
    prompt = f"""You are a data analysis consultant. Build an initial analysis map.

Goal: {goal}
Why it matters: {why}
Available data: {available_data}
Ideas / techniques: {ideas}

Produce:
- Exactly 1 goal node (id: "goal-1") capturing the core objective
- 2–3 data_source nodes (ids: "ds-1", "ds-2", …) named after the described datasets
- 1–2 question nodes (ids: "q-1", "q-2") asking the most important clarifying questions

Connect every data_source to "goal-1" with an edge. Connect "goal-1" to each question node.
Keep descriptions to 1–2 sentences. Questions must be specific and actionable."""
    return _tool_call(prompt)


def generate_research_nodes(nodes: list[Node], goal: str) -> tuple[list[Node], list[Edge]]:
    existing = "\n".join(
        f"  - {n.data.type}: {n.data.label} — {n.data.description}" for n in nodes
    )
    prompt = f"""You are a data analysis consultant expanding an analysis map.

Goal: {goal}
Current map:
{existing}

Add:
- 1–2 technique nodes (ids: "tech-1", "tech-2") suggesting specific analysis methods
- 1 question node (id: "q-r1") with one more important clarifying question

Connect all new nodes to "goal-1"."""
    return _tool_call(prompt, max_tokens=900)


def process_feedback(
    node: Node, all_nodes: list[Node], feedback: str, deeper_research: bool
) -> tuple[list[Node], list[Edge]]:
    goal = next((n.data.label for n in all_nodes if n.data.type == "goal"), "")
    map_summary = "\n".join(
        f"  - {n.data.type} ({n.id}): {n.data.label}" for n in all_nodes
    )
    mode = "deep-research mode: return 2–3 new technique or question nodes" if deeper_research else "return 1 updated or replacement node"
    prompt = f"""You are a data analysis consultant updating an analysis map node.

Overall goal: {goal}
Full map:
{map_summary}

Selected node: {node.data.type} "{node.data.label}" (id: {node.id})
  Description: {node.data.description}

User feedback: {feedback}
Mode: {mode}

Use ids like "fb-1", "fb-2". Connect all new nodes to "goal-1"."""
    return _tool_call(prompt, max_tokens=900)
