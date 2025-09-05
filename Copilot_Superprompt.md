# Copilot Superprompt — Build the Local RAG WebApp (React + FastAPI, Fully Local)

You are my pair-programmer. Implement a **local-only Retrieval-Augmented Generation (RAG) web app** that follows the attached specs in `./docs/`:

- `URD_RAG_WebApp.md` (user needs & constraints).  
- `SRS_RAG_WebApp.md` (functional & non-functional requirements).  
- `HLD_RAG_WebApp.md` (architecture & subsystems).  
- `LLD_RAG_WebApp.md` (React UI + streaming + adaptive chunking/dynamic-k details).  
- `UI_Spec_RAG_WebApp.md` (screens, components, WS events, accessibility, streaming indicator).  

## Hard constraints
- **Everything runs locally/offline**: embeddings, vector search, LLM inference, storage. No cloud calls.
- **Frontend:** React 18 + TypeScript + Vite + Tailwind (and shadcn/ui, lucide-react). **Must stream** tokens with an animated indicator per UI spec.
- **Backend:** Python FastAPI + WebSocket streaming + file uploads, strictly following endpoints & events in LLD/UI Spec.
- **Vector store:** **Qdrant (local)** with payload filters; ok to use Docker or local binary.
- **Models:** Local embedding + local LLM via **Ollama** (preferred) or **llama.cpp** adapter.
- **RAG features:** **Adaptive chunking** per doc + **Dynamic-k** per query; optional local reranker toggle.
- Keep resource usage within a typical laptop budget; provide Eco/Balanced/Performance profiles (threads, context, concurrency).

---

### 0) Create repo layout & configs
Create this tree and minimal configs:

```
/docs/               # (already contains the 5 specs)
/backend/
  app/
    __init__.py
    main.py
    api.py
    ws.py
    models.py         # pydantic types
    storage.py        # filesystem ops
    parsing.py        # text extraction, OCR hook (stub)
    chunking.py       # adaptive chunk policy + splitter
    embeddings.py     # local embeddings
    qdrant_index.py   # collection mgmt + search
    retrieval.py      # ANN + reranker + DynamicKController
    llm.py            # Ollama/llama.cpp adapters + streaming
    eval.py           # mini-eval utilities
    settings.py       # profiles, caps, env
    diagnostics.py    # logs, resource monitor
  tests/
    test_chunking.py
    test_dynamic_k.py
    test_api.py
  pyproject.toml
  README.md
/frontend/
  src/
    main.tsx
    App.tsx
    routes.tsx
    components/
      ChatView.tsx
      StreamingIndicator.tsx
      MessageBubble.tsx
      SourcesPanel.tsx
      LibraryView.tsx
      SettingsView.tsx
      StatusBar.tsx
    lib/api.ts
    lib/ws.ts
    types.ts
    styles.css
  index.html
  package.json
  vite.config.ts
  tailwind.config.js
  postcss.config.js
  README.md
/docker/
  docker-compose.yml  # qdrant + (optional) backend
.gitignore
README.md
```

Root `README.md` must include quickstart, local-only note, profiles, and troubleshooting.

---

### 1) Backend (FastAPI) — implement endpoints + WS stream

**Endpoints (REST):**
- `POST /api/documents` (multipart): save file, parse, adaptive chunk, embed, index → return Document.
- `GET /api/documents`: list with filters (tag/status).
- `PATCH /api/documents/{doc_id}`: rename/tags; can flag “needs re-index”.
- `DELETE /api/documents/{doc_id}?secure=true`: delete or secure-delete (overwrite).
- `POST /api/documents/{doc_id}/reindex`: optional manual chunk params override.
- `POST /api/query`: start a query; do retrieval & decide `k`; return `{session_id, turn_id}` for WS.

**WebSocket (token streaming):**
- `WS /ws/stream?session_id=...&turn_id=...`
- Frames (exact):
  - `{"event":"START","meta":{"model":"<name>"}}`
  - `{"event":"TOKEN","text":"..."}` (incremental)
  - `{"event":"CITATION","label":1,"chunkId":"doc#000123"}`
  - `{"event":"END","stats":{"tokens":N,"ms":T}}`
  - `{"event":"ERROR","error_code":"...","detail":"..."}`

**Core modules:**
- `settings.py` — Eco / Balanced / Performance profiles (threads, context, concurrency).
- `parsing.py` — text extraction; OCR hook stub; write `parsed/{doc_id}.json`.
- `chunking.py` — **Adaptive Chunking** policy + structure-aware splitter (headings/tables).
- `embeddings.py` — local embedding model; batch & cache.
- `qdrant_index.py` — collection `rag_chunks` (cosine); payload fields; search & filters.
- `retrieval.py` — ANN search, optional local reranker; **DynamicKController** (ε-gain, coverage, budget guard).
- `llm.py` — **Ollama** (default) or **llama.cpp**; `generate_stream(prompt, params, on_token)` → WS frames.
- `api.py`, `ws.py`, `models.py`, `storage.py`, `diagnostics.py` — types, logging (JSONL), correlation ids.

**Tests (pytest):**
- `test_chunking.py` — policy variance across 5 heterogeneous docs.
- `test_dynamic_k.py` — k increases for broad queries, respects context budget.
- `test_api.py` — upload → index → query → citations roundtrip.

**Backend deps:** FastAPI, uvicorn, pydantic, python-multipart, qdrant-client, sentence-transformers (or alt), numpy, tokenizers, orjson, httpx, websockets, pytest+coverage.

---

### 2) Frontend (React + Vite + TS + Tailwind + shadcn/ui)

**Components:**
- `ChatView.tsx` — prompt input, transcript (`role="log"`), status badges, **StreamingIndicator**.
- `StreamingIndicator.tsx` — animated typing dots/spinner; `prefers-reduced-motion`; `role="status"`.
- `MessageBubble.tsx` — assistant bubble streams; inline `[1][2]` citations clickable.
- `SourcesPanel.tsx` — top-k list with scores, snippet previews, coverage bar; click `[n]` to focus.
- `LibraryView.tsx` — upload drag-drop; table with name/type/pages/size/tags/status; actions (rename, tag, reindex, delete, secure delete).
- `SettingsView.tsx` — profiles, chunking Auto/Manual, `k_min/k_max`, model presets, encryption toggle.
- `StatusBar.tsx` — offline badge, CPU/RAM, indexing progress.

**Types:** Profile, DocRow, SourceItem, Citation, ChatTurn, UiStatus.  
**Libs:** `lib/api.ts` (REST), `lib/ws.ts` (WS `START/TOKEN/CITATION/END/ERROR` handlers).  
**Styling:** Tailwind + shadcn/ui; lucide-react icons; respect reduced-motion and 4.5:1 contrast.

**Optional E2E:** Playwright test to assert streaming tokens & indicator visibility logic.

---

### 3) RAG algorithms

- **Adaptive Chunking** (`chunking.py`): choose chunk size 500–1350 tokens with 15–25% overlap; use density, heading-rate, tables, script; log rationale.
- **Dynamic-k** (`retrieval.py`): start `k_min`, grow until marginal gain < ε or context budget ≈90%, clamp ≤ `k_max`; log chosen `k`.
- **Prompting:** system prompt enforces grounding; if unsupported by sources → say so.

---

### 4) Local services & run

**docker/docker-compose.yml:** Qdrant on `localhost:6333` (bind volume).  
**Backend dev:** `uvicorn app.main:app --reload`  
**Frontend dev:** `npm i && npm run dev`  
**Env:** `OLLAMA_HOST`, `QDRANT_URL`, `RAG_PROFILE`.

---

### 5) Definition of Done

- Ingest pipeline: upload→parse→**adaptive chunk**→embed→index; visible statuses.  
- Query pipeline: retrieve→**dynamic-k**→stream tokens via WS; inline citations; Sources panel shows chunks, scores, coverage.  
- React UI: layout & a11y per spec; **animated indicator** works; keyboard nav solid.  
- Verified **local-only** with NIC off.  
- Basic tests pass; README quickstart included.

---

### 6) Execution order

1. Backend scaffolding (`main.py`, `api.py`, `ws.py`, `models.py`).  
2. Storage & parsing (`storage.py`, `parsing.py`).  
3. Adaptive chunking (`chunking.py`).  
4. Embeddings & Qdrant (`embeddings.py`, `qdrant_index.py`).  
5. Retrieval & dynamic-k (`retrieval.py`).  
6. LLM streaming (`llm.py`).  
7. Wire routes & WS.  
8. Frontend scaffold & components.  
9. Tests (pytest + a few RTL tests).

**Use these instructions exactly when generating files and code.** Create files with content, not placeholders, and explain any deviations inline with TODOs.
