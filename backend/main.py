from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import context, research, feedback, approve, stream

app = FastAPI(title="Dattack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(context.router)
app.include_router(research.router)
app.include_router(feedback.router)
app.include_router(approve.router)
app.include_router(stream.router)
