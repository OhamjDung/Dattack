import uuid
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse
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
    nodes, edges = generate_initial_map(goal, why, available_data, ideas)

    # Store csv_bytes + goal under a temporary key so /approve can retrieve it
    session_id = str(uuid.uuid4())
    session_data: dict = {"goal": goal, "pending": True}
    if file is not None:
        contents = await file.read()
        session_data["csv_bytes"] = contents
        session_data["filename"] = file.filename

    session_store.save(f"pending_{session_id}", session_data)

    return JSONResponse({
        "nodes": [n.model_dump() for n in nodes],
        "edges": [e.model_dump() for e in edges],
        "pending_session_id": session_id,
    })
