import asyncio
import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi

from personality import build_system_prompt, detect_mode

load_dotenv()

CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com"
    f"/v1beta/models/{GEMINI_MODEL}:streamGenerateContent"
)


class ChunRAG:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.chunks: list[dict] = []
        self.bm25: BM25Okapi | None = None
        self._index_knowledge()

    # ── Indexing ──────────────────────────────────────────────────────────────

    def _chunk(self, text: str) -> list[str]:
        words = text.split()
        step = CHUNK_SIZE - CHUNK_OVERLAP
        chunks = []
        for i in range(0, len(words), step):
            chunk = " ".join(words[i : i + CHUNK_SIZE])
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    def _index_knowledge(self):
        knowledge_dir = Path(__file__).parent / "knowledge"
        self.chunks = []

        for md_file in sorted(knowledge_dir.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            for chunk in self._chunk(text):
                self.chunks.append({"text": chunk, "source": md_file.name})

        if self.chunks:
            tokenized = [c["text"].lower().split() for c in self.chunks]
            self.bm25 = BM25Okapi(tokenized)

    def reindex(self) -> int:
        self._index_knowledge()
        return len(self.chunks)

    # ── Retrieval (BM25) ──────────────────────────────────────────────────────

    def _retrieve(self, query: str, n: int = 4) -> list[str]:
        if not self.bm25 or not self.chunks:
            return []
        scores = self.bm25.get_scores(query.lower().split())
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]
        return [self.chunks[i]["text"] for i in top if scores[i] > 0]

    # ── Generation (REST direto, sem SDK) ─────────────────────────────────────

    async def stream_response(self, message: str, history: list[dict]):
        mode = detect_mode(message)
        context_docs = await asyncio.to_thread(self._retrieve, message)
        context = "\n\n---\n\n".join(context_docs)
        system_prompt = build_system_prompt(mode, context)

        contents = []
        for msg in history[-12:]:
            contents.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": message}]})

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"temperature": 0.9, "maxOutputTokens": 800},
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                GEMINI_URL,
                params={"key": self.api_key, "alt": "sse"},
                json=payload,
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    yield f"*[erro {response.status_code}: {body.decode()[:200]}]*"
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:].strip()
                    if not raw or raw == "[DONE]":
                        continue
                    try:
                        data = json.loads(raw)
                        for candidate in data.get("candidates", []):
                            for part in candidate.get("content", {}).get("parts", []):
                                if "text" in part:
                                    yield part["text"]
                    except json.JSONDecodeError:
                        continue
