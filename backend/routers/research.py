from fastapi import APIRouter
from schemas.models import ResearchRequest, ResearchResponse
from services.placeholder import research_nodes

router = APIRouter()


@router.post("/research", response_model=ResearchResponse)
async def run_research(body: ResearchRequest):
    new_nodes, new_edges = research_nodes()
    return ResearchResponse(new_nodes=new_nodes, new_edges=new_edges)
