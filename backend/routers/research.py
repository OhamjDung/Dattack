from __future__ import annotations
import io

import pandas as pd
from fastapi import APIRouter

from analysis.context import AnalysisContext
from analysis.curiosity_runner import run_curiosity_pipeline
from schemas.models import ResearchRequest, ResearchResponse
from services.gemini_service import generate_research_nodes
from services import session_store

router = APIRouter()

MAX_ITERATIONS = 8


@router.post("/research", response_model=ResearchResponse)
async def run_research(body: ResearchRequest):
    goal = next((n.data.label for n in body.nodes if n.data.type == "goal"), "")

    session_data = session_store.get(f"pending_{body.session_id}")
    curiosity_outputs = None
    iteration = 1

    if session_data:
        csv_bytes = session_data.get("csv_bytes")
        iteration = session_data.get("research_iteration", 1)

        if iteration > MAX_ITERATIONS:
            return ResearchResponse(new_nodes=[], new_edges=[], has_more=False)

        if csv_bytes:
            try:
                df = pd.read_csv(io.BytesIO(csv_bytes))
                ctx = AnalysisContext(df=df, goal=goal)
                curiosity_outputs = await run_curiosity_pipeline(ctx)
            except Exception:
                curiosity_outputs = session_data.get("curiosity_outputs")
        else:
            curiosity_outputs = session_data.get("curiosity_outputs")

        session_store.update(f"pending_{body.session_id}", {"research_iteration": iteration + 1})

    new_nodes, new_edges, has_more = generate_research_nodes(
        body.nodes, goal, curiosity_outputs, iteration
    )

    return ResearchResponse(new_nodes=new_nodes, new_edges=new_edges, has_more=has_more)
