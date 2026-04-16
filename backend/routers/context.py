from fastapi import APIRouter
from schemas.models import ContextRequest, ContextResponse
from services.placeholder import initial_map

router = APIRouter()


@router.post("/context", response_model=ContextResponse)
async def create_context(body: ContextRequest):
    nodes, edges = initial_map(body.goal)
    return ContextResponse(nodes=nodes, edges=edges)
