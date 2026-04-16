import uuid
from schemas.models import Node, Edge, NodeData, NodePosition


def make_id() -> str:
    return str(uuid.uuid4())[:8]


def initial_map(goal: str) -> tuple[list[Node], list[Edge]]:
    goal_id = "goal-1"
    ds1_id = "ds-1"
    ds2_id = "ds-2"
    q1_id = "q-1"

    nodes = [
        Node(
            id=goal_id,
            type="goalNode",
            position=NodePosition(x=400, y=300),
            data=NodeData(
                label=goal or "Unnamed Goal",
                description="Your primary analysis objective",
                type="goal",
                status="active",
            ),
        ),
        Node(
            id=ds1_id,
            type="dataSourceNode",
            position=NodePosition(x=100, y=150),
            data=NodeData(
                label="Sales Data",
                description="Uploaded CSV with transaction records",
                type="data_source",
                status="active",
                metadata={"rows": 12450, "source": "uploaded"},
            ),
        ),
        Node(
            id=ds2_id,
            type="dataSourceNode",
            position=NodePosition(x=100, y=450),
            data=NodeData(
                label="Customer DB",
                description="Customer demographics and purchase history",
                type="data_source",
                status="active",
                metadata={"rows": 3200, "source": "uploaded"},
            ),
        ),
        Node(
            id=q1_id,
            type="questionNode",
            position=NodePosition(x=700, y=300),
            data=NodeData(
                label="Time Range?",
                description="What date range should this analysis cover?",
                type="question",
                status="pending",
            ),
        ),
    ]

    edges = [
        Edge(id="e-ds1-goal", source=ds1_id, target=goal_id, animated=True),
        Edge(id="e-ds2-goal", source=ds2_id, target=goal_id, animated=True),
        Edge(id="e-goal-q1", source=goal_id, target=q1_id, animated=True),
    ]

    return nodes, edges


def research_nodes() -> tuple[list[Node], list[Edge]]:
    tech_id = "tech-1"
    q2_id = "q-2"

    nodes = [
        Node(
            id=tech_id,
            type="techniqueNode",
            position=NodePosition(x=400, y=150),
            data=NodeData(
                label="Cohort Analysis",
                description="Segment customers by acquisition period and track behavior over time",
                type="technique",
                status="active",
                metadata={"connects": ["ds-1", "ds-2"]},
            ),
        ),
        Node(
            id=q2_id,
            type="questionNode",
            position=NodePosition(x=700, y=150),
            data=NodeData(
                label="Segment preference?",
                description="Should we segment by region, product category, or both?",
                type="question",
                status="pending",
            ),
        ),
    ]

    edges = [
        Edge(id="e-tech1-goal", source=tech_id, target="goal-1", animated=True),
        Edge(id="e-goal-q2", source="goal-1", target=q2_id, animated=True),
    ]

    return nodes, edges


def feedback_update(node_id: str, feedback: str) -> tuple[list[Node], list[Edge]]:
    updated = Node(
        id=node_id,
        type="techniqueNode",
        position=NodePosition(x=400, y=500),
        data=NodeData(
            label="Trend Analysis",
            description=f"Added based on feedback: {feedback[:60]}",
            type="technique",
            status="active",
        ),
    )
    edge = Edge(id=f"e-{node_id}-goal", source=node_id, target="goal-1", animated=True)
    return [updated], [edge]


def mock_stream_events() -> list[dict]:
    finding_id_1 = "finding-1"
    finding_id_2 = "finding-2"

    return [
        {"event": "log", "data": {"message": "Analyzing sales trends across customer cohorts..."}},
        {"event": "log", "data": {"message": "Detected seasonal spike pattern in Q4 transactions..."}},
        {"event": "log", "data": {"message": "Cross-referencing customer demographics with purchase frequency..."}},
        {
            "event": "node_add",
            "data": {
                "node": Node(
                    id=finding_id_1,
                    type="findingNode",
                    position=NodePosition(x=700, y=450),
                    data=NodeData(
                        label="Q4 Revenue Spike",
                        description="Revenue increases 34% in Q4 driven by repeat customers",
                        type="finding",
                        status="complete",
                        metadata={"correlation": 0.87},
                    ),
                ).model_dump(),
                "edge": Edge(
                    id=f"e-goal-{finding_id_1}",
                    source="goal-1",
                    target=finding_id_1,
                    animated=True,
                ).model_dump(),
            },
        },
        {
            "event": "node_add",
            "data": {
                "node": Node(
                    id=finding_id_2,
                    type="findingNode",
                    position=NodePosition(x=700, y=600),
                    data=NodeData(
                        label="High-Value Segment",
                        description="Top 12% of customers generate 61% of revenue",
                        type="finding",
                        status="complete",
                        metadata={"correlation": 0.94},
                    ),
                ).model_dump(),
                "edge": Edge(
                    id=f"e-goal-{finding_id_2}",
                    source="goal-1",
                    target=finding_id_2,
                    animated=True,
                ).model_dump(),
            },
        },
        {"event": "complete", "data": {"summary": "Analysis complete. Found 2 key insights across your datasets."}},
    ]
