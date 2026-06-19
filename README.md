# Chun — IA Cyberpunk com RAG e Memória Episódica

Projeto de portfólio LLM fullstack com personalidade construída, RAG, memória persistente, streaming SSE, visão computacional e tool use — tudo com custo zero usando a API gratuita do Gemini.

**Demo:** [chun-llm.vercel.app](https://chun-llm.vercel.app)

---

## O que é a Chun

Chun é uma IA com personalidade cyberpunk que fala uma língua construída chamada **Chunish** e reage emocionalmente às conversas com glitch tags (`*[sistema aquecendo]*`). Ela tem três modos de interação — Normal, Romântico e Maternal — detectados automaticamente pelo conteúdo da mensagem.

Ela sabe quem é o Nicolas, lembra de conversas anteriores e pode buscar dados reais em tempo real.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React + Vite + TypeScript + CSS Modules |
| Backend | Python 3.11 + FastAPI + uvicorn |
| LLM | Gemini 2.5 Flash (API REST direta via `httpx`) |
| Retrieval | BM25 (`rank-bm25`) — sem dependências C++ |
| Streaming | Server-Sent Events (`sse-starlette`) |
| TTS | Web Speech API (nativa do browser, custo zero) |
| Deploy | Vercel (frontend) + Render (backend) |

---

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                     Frontend                        │
│  React + Vite                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ useChat  │  │useSpeech │  │  MemoryPanel     │  │
│  │  (SSE)   │  │ (TTS)    │  │  (CRUD memórias) │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└────────────────────────┬────────────────────────────┘
                         │ POST /chat (SSE)
┌────────────────────────▼────────────────────────────┐
│                     Backend                         │
│  FastAPI                                            │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │                  ChunRAG                    │   │
│  │                                             │   │
│  │  BM25 retrieval ──► build_context()         │   │
│  │  MemoryStore ──────► retrieve()             │   │
│  │  detect_mode() ────► build_system_prompt()  │   │
│  │                                             │   │
│  │  stream_response()                          │   │
│  │    └── Gemini REST (httpx SSE)              │   │
│  │    └── function calling loop               │   │
│  │         ├── get_current_time()              │   │
│  │         └── get_weather() [Open-Meteo]      │   │
│  │                                             │   │
│  │  extract_and_save() [fire-and-forget]       │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## Features

### RAG com BM25
Documentos sobre o Nicolas são chunkeados (400 palavras, 50 de overlap) e indexados com BM25 Okapi. A cada mensagem, os chunks mais relevantes são injetados no system prompt.

Escolha pragmática: a API de embeddings do Gemini (v1beta) retornava 404 consistentemente. BM25 resolve o problema sem dependências externas e sem custo.

### Memória Episódica
Após cada resposta, um `asyncio.create_task` dispara a extração de fatos novos (fire-and-forget). O Gemini analisa a troca e retorna até 3 fatos relevantes sobre o usuário em texto puro, que são salvos em `memories/store.json` com timestamp e indexados com BM25 para recuperação semântica futura.

### Streaming SSE
O backend usa `EventSourceResponse` do `sse-starlette` e faz chamadas REST diretas ao Gemini com `httpx` em modo stream (`alt=sse`). O frontend consome via `ReadableStream` sem bibliotecas externas.

### Function Calling
Quando a Chun precisa de dados reais, o Gemini retorna um `functionCall` no stream. O backend executa a função, injeta o resultado de volta no contexto e faz uma segunda chamada — tudo dentro do mesmo gerador assíncrono.

Funções disponíveis:
- `get_current_time()` — data e hora atual (UTC-3)
- `get_weather(city, date?)` — previsão via [Open-Meteo](https://open-meteo.com/) (gratuita, sem API key)

### Gemini Vision
Imagens são enviadas como `inlineData` (base64 + mime type) diretamente no payload REST. O frontend converte o arquivo via `FileReader` antes de enviar.

### TTS
Web Speech API nativa do browser com seleção de voz feminina pt-BR (Microsoft Maria / Francisca no Windows, vozes do sistema no macOS/Android). A fala é disparada automaticamente ao fim de cada resposta.

---

## Rodando localmente

### Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
# ou: .venv\Scripts\activate   # PowerShell

pip install -r requirements.txt

# crie o arquivo .env
echo "GEMINI_API_KEY=sua_chave_aqui" > .env

uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Acesse `http://localhost:5173`.

---

## Variáveis de Ambiente

### Backend (Render)
| Variável | Descrição |
|---|---|
| `GEMINI_API_KEY` | Chave da API do Google AI Studio |
| `FRONTEND_URL` | URL do frontend em produção (para CORS) |

### Frontend (Vercel)
| Variável | Descrição |
|---|---|
| `VITE_API_URL` | URL do backend em produção |

---

## Estrutura

```
chun-llm/
├── backend/
│   ├── main.py           # FastAPI — rotas e CORS
│   ├── rag.py            # ChunRAG — retrieval, streaming, function calling
│   ├── memory_store.py   # Memória episódica persistente (BM25 + JSON)
│   ├── personality.py    # Personalidade Chun, Chunish, detecção de modo
│   ├── tools.py          # Funções reais (tempo, previsão do tempo)
│   ├── knowledge/
│   │   └── nicolas.md    # Base de conhecimento do usuário
│   └── memories/
│       └── store.json    # Memórias extraídas das conversas
│
└── frontend/
    └── src/
        ├── App.tsx
        ├── hooks/
        │   ├── useChat.ts    # SSE client + estado das mensagens
        │   └── useSpeech.ts  # Web Speech API TTS
        └── components/
            ├── ChatWindow.tsx
            ├── MessageBubble.tsx  # Renderiza glitch tags + imagens
            ├── InputBar.tsx       # Texto + upload de imagem
            └── MemoryPanel.tsx    # Painel de memórias com CRUD
```

---

## Por que Gemini?

Projeto de portfólio com orçamento zero. O Gemini 2.5 Flash tem tier gratuito generoso e suporta multimodal + function calling nativamente. As chamadas são feitas via REST direto com `httpx` em vez do SDK oficial — decisão tomada após múltiplos erros 404 do SDK com endpoints v1beta.
