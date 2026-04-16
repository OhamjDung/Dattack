from fastapi import APIRouter, HTTPException
from schemas.models import FeedbackRequest, FeedbackResponse
from services.gemini_service import process_feedback

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(body: FeedbackRequest):
    target = next((n for n in body.nodes if n.id == body.node_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail=f"Node {body.node_id} not found")
    updated_nodes, new_edges = process_feedback(
        target, body.nodes, body.feedback, body.deeper_research
    )
    return FeedbackResponse(updated_nodes=updated_nodes, new_edges=new_edges)
