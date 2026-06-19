import json

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

load_dotenv()

from rag import ChunRAG

app = FastAPI(title="Chun API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chun = ChunRAG()


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    image: str | None = None  # base64 data URL


@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate():
        async for chunk in chun.stream_response(req.message, req.history, req.image):
            yield {"data": json.dumps(chunk)}

    return EventSourceResponse(generate())


@app.get("/memories")
async def get_memories():
    return {"memories": chun.memory.all()}


@app.delete("/memories/{index}")
async def delete_memory(index: int):
    actual = len(chun.memory.memories) - 1 - index
    if 0 <= actual < len(chun.memory.memories):
        chun.memory.memories.pop(actual)
        chun.memory._save()
        chun.memory._rebuild_index()
        return {"status": "ok"}
    return {"status": "not found"}

@app.delete("/memories")
async def clear_memories():
    chun.memory.memories = []
    chun.memory._save()
    chun.memory._rebuild_index()
    return {"status": "ok"}


@app.post("/reindex")
async def reindex():
    count = chun.reindex()
    return {"status": "ok", "chunks_indexed": count}


@app.get("/health")
async def health():
    return {
        "status": "online",
        "chunks_indexed": len(chun.chunks),
        "memories": len(chun.memory.memories),
    }
