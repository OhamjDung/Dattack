from fastapi import APIRouter
from schemas.models import ResearchRequest, ResearchResponse
from services.gemini_service import generate_research_nodes

router = APIRouter()


@router.post("/research", response_model=ResearchResponse)
async def run_research(body: ResearchRequest):
    goal = next((n.data.label for n in body.nodes if n.data.type == "goal"), "")
    new_nodes, new_edges = generate_research_nodes(body.nodes, goal)
    return ResearchResponse(new_nodes=new_nodes, new_edges=new_edges)
