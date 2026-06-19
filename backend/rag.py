import asyncio
import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi

from memory_store import MemoryStore
from personality import build_system_prompt, detect_mode
from tools import TOOLS_SCHEMA, execute_tool

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
        self.memory = MemoryStore(api_key=self.api_key)
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

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def _retrieve_knowledge(self, query: str, n: int = 4) -> list[str]:
        if not self.bm25 or not self.chunks:
            return []
        scores = self.bm25.get_scores(query.lower().split())
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]
        return [self.chunks[i]["text"] for i in top if scores[i] > 0]

    def _build_context(self, query: str) -> str:
        knowledge = self._retrieve_knowledge(query)
        memories = self.memory.retrieve(query)

        parts = []
        if knowledge:
            parts.append("## Conhecimento sobre o Nicolas\n" + "\n\n".join(knowledge))
        if memories:
            bullet_memories = "\n".join(f"- {m}" for m in memories)
            parts.append(f"## Memórias das nossas conversas\n{bullet_memories}")

        return "\n\n".join(parts)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_contents(self, history: list[dict], message: str, image: str | None) -> list[dict]:
        contents = []
        for msg in history[-12:]:
            contents.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})

        user_parts: list[dict] = [{"text": message}]
        if image:
            if "," in image:
                header, data = image.split(",", 1)
                mime_type = header.split(":")[1].split(";")[0]
            else:
                data, mime_type = image, "image/jpeg"
            user_parts.append({"inlineData": {"mimeType": mime_type, "data": data}})

        contents.append({"role": "user", "parts": user_parts})
        return contents

    async def _stream_gemini(self, client: httpx.AsyncClient, payload: dict):
        """Itera sobre uma chamada SSE do Gemini, yielding (text, function_call)."""
        async with client.stream(
            "POST",
            GEMINI_URL,
            params={"key": self.api_key, "alt": "sse"},
            json=payload,
        ) as response:
            if response.status_code != 200:
                body = await response.aread()
                yield f"*[erro {response.status_code}: {body.decode()[:200]}]*", None
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
                                yield part["text"], None
                            elif "functionCall" in part:
                                yield None, part["functionCall"]
                except json.JSONDecodeError:
                    continue

    # ── Generation (streaming REST + function calling) ────────────────────────

    async def stream_response(self, message: str, history: list[dict], image: str | None = None):
        mode = detect_mode(message)
        context = await asyncio.to_thread(self._build_context, message)
        system_prompt = build_system_prompt(mode, context)

        contents = self._build_contents(history, message, image)

        base_payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"temperature": 0.9, "maxOutputTokens": 800},
            "tools": TOOLS_SCHEMA,
        }

        full_text = ""
        function_call = None

        async with httpx.AsyncClient(timeout=60.0) as client:
            # ── 1ª chamada ────────────────────────────────────────────────────
            async for text, fc in self._stream_gemini(client, {**base_payload, "contents": contents}):
                if text is not None:
                    full_text += text
                    yield text
                elif fc is not None:
                    function_call = fc

            # ── Loop de function calling ──────────────────────────────────────
            while function_call:
                func_name = function_call["name"]
                func_args = function_call.get("args", {})

                print(f"[Tools] Chamando {func_name}({func_args})")
                tool_result = await execute_tool(func_name, func_args)
                print(f"[Tools] Resultado: {tool_result}")

                contents.append({
                    "role": "model",
                    "parts": [{"functionCall": function_call}],
                })
                contents.append({
                    "role": "user",
                    "parts": [{"functionResponse": {
                        "name": func_name,
                        "response": {"result": tool_result},
                    }}],
                })

                full_text = ""
                function_call = None

                async for text, fc in self._stream_gemini(client, {**base_payload, "contents": contents}):
                    if text is not None:
                        full_text += text
                        yield text
                    elif fc is not None:
                        function_call = fc

        if full_text:
            print(f"[RAG] Agendando extração de memória ({len(full_text)} chars)")
            asyncio.create_task(self.memory.extract_and_save(message, full_text))
