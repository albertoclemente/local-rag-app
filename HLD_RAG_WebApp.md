# High-Level Design (HLD)
**System Title:** Local RAG-based Document Q&A WebApp
**Version:** 1.0 (Draft)
**Date:** 04 Sep 2025

---

## 1. Introduction

### 1.1 Purpose
This HLD specifies the architecture of the Local RAG WebApp. It defines the system’s structural components, external interfaces, and data flow, providing a blueprint for developers and testers. It bridges the gap between requirements (SRS) and detailed implementation (LLD).

### 1.2 Scope
The HLD covers:
- Architectural style.
- Subsystems and their responsibilities.
- Component interactions.
- Data storage and flow.
- Constraints from SRS (local, resource-efficient, accurate).

---

## 2. Architectural Design

### 2.1 Architectural Style
- **Client–Server (Localhost only):**
  - **Frontend (Client):** Browser-based UI.
  - **Backend (Server):** Local Python/FastAPI service orchestrating the pipeline.
- **Layered Design:**
  - **Presentation Layer (UI):** Renders the chat interface, document library, and settings.
  - **Application Layer (Backend):** Handles business logic, query orchestration, RAG pipeline, and configuration management.
  - **Data Layer:** Manages the vector store and local document storage.

### 2.2 Major Subsystems

#### 2.2.1 Document Management Subsystem
- **Responsibilities:**
  - Accept user uploads.
  - Extract text, run adaptive chunking.
  - Trigger embeddings and indexing.
  - Manage document metadata (tags, size, date).
- **Interfaces:**
  - File system (read/write).
  - Vector Store (Qdrant).
  - Exposes a **REST API** to the Application Layer.

#### 2.2.2 RAG Engine Subsystem
- **Responsibilities:**
  - Adaptive chunking decision logic.
  - Embedding generation (local embedding model).
  - Similarity search via Qdrant.
  - Dynamic-k retrieval control.
  - Optional reranking.
- **Interfaces:**
  - Vector store API.
  - LLM Engine API.

#### 2.2.3 LLM Engine Subsystem
- **Responsibilities:**
  - Generate responses using retrieved context.
  - Stream output token-by-token.
  - Provide citations in answer text.
- **Interfaces:**
  - RAG Engine (input context).
  - Chat Subsystem (streaming channel).

#### 2.2.4 Chat & UI Subsystem
- **Responsibilities:**
  - Accept queries.
  - Display streaming answers.
  - Maintain chat history.
  - Show citations and retrieved chunks.
- **Interfaces:**
  - Interacts with the Application Layer via a **REST API** for control/management and a **WebSocket** for real-time streaming.
  - User (browser).

#### 2.2.5 Data Storage Subsystem
- **Responsibilities:**
  - Store embeddings and metadata (Qdrant).
  - Maintain secure local storage for docs.
  - Handle export/import of library archives.

---

## 3. Data Design

### 3.1 Data Structures
- **Document Metadata:** {id, name, type, size, page count, tags, index status, chunk params, date added}.
- **Chunk Embedding Record:** {doc_id, chunk_id, text, embedding_vector, metadata}.
- **Chat Log Entry:** {session_id, turn_id, user_query, system_response, citations, timestamp, k_used}.
- **System Configuration:** {profile: 'eco'|'balanced'|'performance', model_paths, rag_params}.

### 3.2 Data Flow
1.  **Upload:** User → Chat & UI Subsystem → Application Layer → Document Management → Parser + Adaptive Chunker → Embeddings → Vector Store.
2.  **Query:** User → Chat & UI Subsystem → Application Layer (Query Orchestrator) → Vector Store (retrieve) → RAG Engine (rerank, dynamic k) → LLM Engine (generate + stream) → Chat & UI Subsystem (display + log).
3.  **Management:** User → Chat & UI Subsystem → Application Layer → Document Management → Vector Store + File System.

---

## 4. Component Interaction

- **Sequence Example (Query):**
  1.  User submits query in chat UI.
  2.  Frontend sends query to backend via **REST API**.
  3.  Backend orchestrator calls Retrieval service (dynamic k).
  4.  Retrieved chunks are sent to the LLM Engine.
  5.  The LLM streams tokens back to the Application Layer, which relays them via **WebSocket**.
  6.  Chat UI receives tokens via WebSocket and displays them incrementally.

---

## 5. Constraints & Design Decisions

- Entirely offline (no cloud calls).
- Qdrant chosen for flexibility (collections, payload filters, quantization).
- Adaptive chunking to maximize retrieval accuracy.
- Dynamic k to balance precision/recall vs. context budget.
- Token streaming for responsiveness.

---

## 6. System Models

### 6.1 Context Diagram