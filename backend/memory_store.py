import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

import httpx
from rank_bm25 import BM25Okapi

STORE_PATH = Path(__file__).parent / "memories" / "store.json"

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com"
    f"/v1beta/models/{GEMINI_MODEL}:generateContent"
)

EXTRACT_PROMPT = """Analise essa troca entre Nicolas e Chun.
Liste até 3 fatos NOVOS e relevantes sobre o Nicolas (sentimentos, planos, acontecimentos, saúde, família).
Responda APENAS com os fatos, um por linha, sem bullet points, sem numeração, sem formatação extra.
Se não houver nada novo, responda apenas: NADA

Usuário: {user_message}
Chun: {chun_response}"""


class MemoryStore:
    def __init__(self, api_key: str):
        self.api_key = api_key
        STORE_PATH.parent.mkdir(exist_ok=True)
        self._load()

    # ── Persistência ──────────────────────────────────────────────────────────

    def _load(self):
        if STORE_PATH.exists():
            with open(STORE_PATH, encoding="utf-8") as f:
                self.memories: list[dict] = json.load(f)
        else:
            self.memories = []
        self._rebuild_index()

    def _save(self):
        with open(STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)

    def _rebuild_index(self):
        if self.memories:
            tokenized = [m["fact"].lower().split() for m in self.memories]
            self.bm25: BM25Okapi | None = BM25Okapi(tokenized)
        else:
            self.bm25 = None

    # ── API pública ───────────────────────────────────────────────────────────

    def retrieve(self, query: str, n: int = 3) -> list[str]:
        if not self.bm25 or not self.memories:
            return []
        scores = self.bm25.get_scores(query.lower().split())
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]
        return [self.memories[i]["fact"] for i in top if scores[i] > 0]

    def add(self, fact: str):
        self.memories.append({"fact": fact, "ts": datetime.now().isoformat()})
        self._save()
        self._rebuild_index()

    def all(self) -> list[dict]:
        return list(reversed(self.memories))

    # ── Extração assíncrona (fire-and-forget) ─────────────────────────────────

    async def extract_and_save(self, user_message: str, chun_response: str):
        print(f"[Memory] Iniciando extração para: {user_message[:60]!r}")
        prompt = EXTRACT_PROMPT.format(
            user_message=user_message,
            chun_response=chun_response,
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512},
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    GEMINI_URL,
                    params={"key": self.api_key},
                    json=payload,
                )
                data = resp.json()
                if resp.status_code != 200:
                    print(f"[Memory] Erro na extração: {resp.status_code} {data}")
                    return
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"[Memory] Resposta bruta: {text!r}")
                lines = [l.strip() for l in text.strip().splitlines()]
                facts = [l for l in lines if l and l.upper() != "NADA" and len(l) > 15][:3]
                for fact in facts:
                    self.add(fact)
                if facts:
                    print(f"[Memory] {len(facts)} fatos salvos: {facts}")
                else:
                    print("[Memory] Nenhum fato novo extraído.")
        except Exception as e:
            print(f"[Memory] Exceção na extração: {e}")
