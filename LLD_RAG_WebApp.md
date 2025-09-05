# Low-Level Design (LLD)
**System:** Local RAG-based Document Q&A WebApp
**Version:** 1.1 (React UI + Animated Streaming Indicator)
**Date:** 04 Sep 2025
**References:** SRS v1.1, HLD v1.0, Sommerville (architecture & design best practices)

---

## 1. Purpose & Scope
This Low-Level Design (LLD) details the concrete components, data models, interfaces, and algorithms required to implement the Local RAG WebApp. It **explicitly specifies a React frontend** and an **animated icon during LLM generation**. It operationalizes the SRS and HLD by specifying class/module responsibilities, REST/WebSocket APIs, data schemas, persistence design, and error handling.

---

## 2. Architectural Recap (from HLD)
- **Frontend (React):** Chat interface with WebSocket streaming; Sources/Why panel; Library/Settings.
- **Backend (Local Service):** FastAPI-like HTTP API + WebSocket for streaming.
- **RAG Engine:** Adaptive Chunking → Embeddings → Qdrant Index → Retrieval → Dynamic-k → (optional) Rerank → LLM Generation (streamed).
- **Storage:** Qdrant (embedded/local) for vectors + filesystem for documents/metadata.

Directory conventions (local user-writable app data folder):
`~/RAGApp/
  config/
  logs/
  models/           # local LLM, embeddings, reranker
  library/raw/      # original uploaded docs
  library/parsed/   # parsed text/json, per doc
  library/indices/  # Qdrant or index snapshots
  exports/          # library export archives
  eval/             # mini-eval corpora & results`

---

## 3. Backend Modules & Responsibilities
(unchanged from v1.0 except where noted for streaming states)

### 3.1 API Gateway (HTTP + WebSocket)
- **Tech:** FastAPI or similar.
- **Responsibilities:**
  - Expose REST endpoints (upload, list, delete, reindex, query, settings).
  - Manage **WebSocket** for streaming LLM output.
  - Enforce offline mode (deny outbound calls except loopback).
- **Key Classes:** `ApiRouter`, `StreamingHub`.
- **Dependencies:** Document Manager, RAG Engine, LLM Engine, Library Manager.

### 3.2–3.10
Document Manager, Adaptive Chunker, Embedding Service, Indexer (Qdrant), Retriever (+ Dynamic-k), LLM Engine, Chat Service, Evaluation, Diagnostics & Logging — *as in LLD v1.0.*

---

## 4. React Frontend Components

### 4.1 Technology & Standards
- **Framework:** React 18+ with Vite.
- **Language:** TypeScript.
- **State Management:** **Zustand** will be used for global client state (e.g., UI theme, sidebar state). **React Query (TanStack Query)** will be used for managing server state, caching, and data fetching.
- **Streaming:** Native **WebSocket** client for token streaming.
- **Accessibility:** WCAG 2.1 AA; ARIA roles for live regions; **prefers-reduced-motion** respected.

### 4.2 Recommended Frontend Directory Structure
`/src
  /api/         # API client, WebSocket handler
  /assets/      # SVGs, images
  /components/  # Reusable UI components (e.g., MessageBubble, StreamingIndicator)
  /features/    # Feature-based components (e.g., chat, library, settings)
  /hooks/       # Custom hooks
  /lib/         # Utility functions
  /state/       # Zustand stores
  /types/       # Global TypeScript types
  App.tsx
  main.tsx`

### 4.3 Views & Components
- `ChatView`
  - **Input**: multiline text box, submit hotkey `Ctrl/Cmd+Enter`.
  - **Transcript**: virtualized list for long sessions.
  - **Status Badges**: “Retrieving…”, “Streaming…”, “Complete”.
  - **Animated Indicator**: `StreamingIndicator` visible when `status === "STREAMING"`.
- `StreamingIndicator` (**new**)
  - Animated icon shown during generation (spinner, typing dots).
  - **A11y**: Uses `aria-live="polite"`; respects `prefers-reduced-motion`.
- `SourcesPanel`
  - Inline citations; snippet previews; scores; coverage meter.
- `LibraryView`
  - Upload/drag-drop; table with file metadata; actions (re-index, delete, etc.).
- `SettingsView`
  - Performance profiles; chunking mode; model presets; context budget; encryption toggle.
- `EvalView` (optional)

### 4.4 Component Contracts (TypeScript)
`type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: Array<{label: number; docId: string; chunkId: string; pageStart?: number}>;
  createdAt: string;
};

type UiStatus = "idle" | "retrieving" | "streaming" | "complete" | "error";

type StreamEvent =
  | { event: "START"; meta: { model: string } }
  | { event: "TOKEN"; text: string }
  | { event: "CITATION"; label: number; chunkId: string }
  | { event: "END"; stats: { tokens: number; ms: number } }
  | { event: "ERROR"; error_code: string; detail: string };

interface StreamingIndicatorProps {
  state: UiStatus;
  label?: string;
}`

### 4.5 UI States & Animated Indicator Logic
- **States:** `IDLE → RETRIEVING → STREAMING → COMPLETE` (or `ERROR`).
- **Indicator behavior:**
  - RETRIEVING ⇒ subtle spinner.
  - STREAMING ⇒ animated typing dots (`…`).
  - **Reduced motion:** replace animation with a periodic pulsing dot.
- **ARIA:** `role="status"` and `aria-live="polite"` on a hidden textual description.

---

## 5. Data Models & JSON Schemas
(unchanged key structures)

### 5.1 Chat UI Status (Zustand store slice)
`{
  "status": "idle | retrieving | streaming | complete | error",
  "currentTurnId": 12,
  "model": "local-llm-small"
}`

---

## 6. Service Interfaces (API)

### 6.1 REST Endpoints
- `POST /api/documents` — upload file (multipart); returns `Document`.
- `GET /api/documents` — list documents (filters: tag, status).
- `PATCH /api/documents/{doc_id}`
  - **Request Body:** `{ "name"?: string, "tags"?: string[] }`
  - **Response:** `200 OK` with updated `Document`.
- `DELETE /api/documents/{doc_id}?secure=true` — delete; `secure` is optional boolean.
- `POST /api/documents/{doc_id}/reindex`
- `POST /api/query`
  - **Request Body:** `{ "query": string, "sessionId": string }`
  - **Response:** `{ "turnId": string, "sessionId": string }`

### 6.2 WebSocket (Streaming)
- Endpoint: `WS /ws/stream?session_id=...&turn_id=...`
- Events: `START`, `TOKEN`, `CITATION`, `END`, `ERROR` (see types above).

---

## 7. Core Algorithms (unchanged)
- **Adaptive Chunking:** heuristic selection of chunk tokens and overlap.
- **Dynamic-k:** stop rules by marginal score gain, coverage plateau, and budget.
- **Coverage Meter & Reranker:** as defined in LLD v1.0.

---

## 8. Testing Additions (UI/Streaming)
- **Visual:** Indicator appears during RETRIEVING/STREAMING and hides on COMPLETE/ERROR.
- **Timing:** Time-to-first-token ≤ 1.5 s (95th percentile).
- **A11y:** Indicator has accessible status text; honors reduced-motion.
- **E2E:** WebSocket drops gracefully revert indicator to ERROR state and show retry.

---

## 9. Traceability (Delta from LLD v1.0)
- **SRS FR-11 (Streaming):** `StreamingIndicator`, WebSocket handling.
- **SRS FR-12 (Chat log):** React ChatView with virtualized list.
- **UI Constraint (React):** Frontend explicitly React-based.

---

*End of LLD v1.1 (React + Animated Streaming Indicator).*