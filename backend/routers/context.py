from __future__ import annotations
import io
import uuid

import pandas as pd
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from analysis.context import AnalysisContext
from analysis.curiosity_runner import run_curiosity_pipeline
from schemas.models import ContextResponse
from services.gemini_service import generate_initial_map
from services import session_store

router = APIRouter()


@router.post("/context", response_model=ContextResponse)
async def create_context(
    goal: str = Form(...),
    why: str = Form(""),
    available_data: str = Form(""),
    ideas: str = Form(""),
    file: UploadFile = File(None),
):
    session_id = str(uuid.uuid4())
    session_data: dict = {"goal": goal, "pending": True}
    curiosity_outputs = None

    if file is not None:
        contents = await file.read()
        session_data["csv_bytes"] = contents
        session_data["filename"] = file.filename

        try:
            df = pd.read_csv(io.BytesIO(contents))
            ctx = AnalysisContext(df=df, goal=goal)
            curiosity_outputs = await run_curiosity_pipeline(ctx)
            session_data["curiosity_outputs"] = curiosity_outputs
        except Exception:
            curiosity_outputs = None

    nodes, edges = generate_initial_map(goal, why, available_data, ideas, curiosity_outputs)

    session_store.save(f"pending_{session_id}", session_data)

    return JSONResponse({
        "nodes": [n.model_dump() for n in nodes],
        "edges": [e.model_dump() for e in edges],
        "pending_session_id": session_id,
    })
