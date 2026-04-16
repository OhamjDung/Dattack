import uuid
from fastapi import APIRouter
from schemas.models import ApproveRequest, ApproveResponse
from services import session_store

router = APIRouter()


@router.post("/approve", response_model=ApproveResponse)
async def approve_map(body: ApproveRequest):
    session_id = str(uuid.uuid4())
    goal = next((n.data.label for n in body.nodes if n.data.type == "goal"), "")

    # Merge with pending session if CSV was uploaded
    pending_data = {}
    if body.pending_session_id:
        pending_data = session_store.get(f"pending_{body.pending_session_id}") or {}

    session_store.save(session_id, {
        **pending_data,
        "nodes": [n.model_dump() for n in body.nodes],
        "edges": [e.model_dump() for e in body.edges],
        "goal": goal,
    })
    return ApproveResponse(session_id=session_id, status="analysis_started")
