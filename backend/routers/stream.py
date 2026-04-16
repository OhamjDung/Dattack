from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from services import session_store
from services.script_stream import run_and_stream

router = APIRouter()


@router.get("/stream")
async def stream_endpoint(session_id: str):
    data = session_store.get(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session not found")

    async def generator():
        async for event in run_and_stream(data):
            yield event

    return EventSourceResponse(generator())
