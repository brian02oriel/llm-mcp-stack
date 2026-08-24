import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config import settings
from orchestrator import fetch_tool_schemas, run_conversation

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.tool_schemas = await fetch_tool_schemas()
    yield


app = FastAPI(title="LLM + MCP Gateway", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        return await run_conversation(req.message, app.state.tool_schemas)
    except Exception as exc:
        logging.exception("chat failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.llm_model,
            "tools": [t["function"]["name"] for t in app.state.tool_schemas]}