import uuid
from fastapi import APIRouter
from schemas.models import ApproveRequest, ApproveResponse

router = APIRouter()


@router.post("/approve", response_model=ApproveResponse)
async def approve_map(body: ApproveRequest):
    session_id = str(uuid.uuid4())
    return ApproveResponse(session_id=session_id, status="analysis_started")
