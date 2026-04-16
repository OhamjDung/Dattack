import asyncio
import json
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from services.placeholder import mock_stream_events

router = APIRouter()


@router.get("/stream")
async def stream_analysis():
    async def event_generator():
        events = mock_stream_events()
        for item in events:
            await asyncio.sleep(1.2)
            yield {"event": item["event"], "data": json.dumps(item["data"])}

    return EventSourceResponse(event_generator())
