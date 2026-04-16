from fastapi import APIRouter
from schemas.models import FeedbackRequest, FeedbackResponse
from services.placeholder import feedback_update

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(body: FeedbackRequest):
    updated_nodes, new_edges = feedback_update(body.node_id, body.feedback)
    return FeedbackResponse(updated_nodes=updated_nodes, new_edges=new_edges)
