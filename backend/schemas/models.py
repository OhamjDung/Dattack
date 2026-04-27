from pydantic import BaseModel
from typing import Any, Literal, Optional


NodeType = Literal["goal", "data_source", "technique", "question", "finding", "insight"]
NodeStatus = Literal["pending", "active", "answered", "complete", "low_confidence"]


class NodeData(BaseModel):
    label: str
    description: str
    type: NodeType
    status: Optional[NodeStatus] = None
    metadata: Optional[dict[str, Any]] = None


class NodePosition(BaseModel):
    x: float
    y: float


class Node(BaseModel):
    id: str
    type: str = "custom"
    position: NodePosition
    data: NodeData


class Edge(BaseModel):
    id: str
    source: str
    target: str
    animated: bool = False


class ContextRequest(BaseModel):
    goal: str
    why: str
    available_data: str
    ideas: str


class ResearchRequest(BaseModel):
    session_id: str
    nodes: list["Node"] = []


class FeedbackRequest(BaseModel):
    node_id: str
    feedback: str
    deeper_research: bool = False
    nodes: list["Node"] = []


class ApproveRequest(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
    pending_session_id: Optional[str] = None


class ContextResponse(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
    pending_session_id: Optional[str] = None


class ResearchResponse(BaseModel):
    new_nodes: list[Node]
    new_edges: list[Edge]
    has_more: bool = False


class FeedbackResponse(BaseModel):
    updated_nodes: list[Node]
    new_edges: list[Edge]


class ApproveResponse(BaseModel):
    session_id: str
    status: Literal["analysis_started"]
