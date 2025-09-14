# Local RAG WebApp

A completely local Retrieval-Augmented Generation (RAG) web app for document Q&A. Upload your documents, ask questions, and get accurate, properly formatted answers — no cloud required.

## ✨ Features

- 100% local: data never leaves your machine
- Multi-format: PDF, DOCX, TXT, MD, EPUB
- Smart RAG: adaptive chunking + dynamic-k retrieval
- Streaming replies: live token streaming over WebSocket
- Sources panel: see which documents informed each answer
- Profiles: Eco / Balanced / Performance
- Modern UI: Next.js (React + TypeScript)

## � Simple Start (No Git Needed)
## Simple Start (No Git Needed — for non‑experts)

No Git required: download the ZIP and run the one‑command script.
This is the easiest path for non‑experts on macOS.

For developers comfortable with Git and the command line. Please note that this section assumes familiarity with Git commands and the terminal.
- Docker Desktop: https://www.docker.com/products/docker-desktop/
- Ollama (Local LLM): https://ollama.ai/
- Node.js 18+ (LTS): https://nodejs.org/ or `brew install node`
- Python 3.9+ (macOS usually has `python3` preinstalled)

2) Download the app (ZIP)
- Open the project page in your browser: https://github.com/albertoclemente/local-rag-app
- Click the green “Code” button → “Download ZIP”
- Unzip it (double‑click). You’ll get a folder like `local-rag-app-main`.

3) Start everything automatically (one command)
- Open Terminal and run these commands (adjust the path as needed):

```bash
cd ~/Downloads/local-rag-app-main
chmod +x scripts/quick_try.sh
./scripts/quick_try.sh
```

- When it finishes starting, open the UI: http://localhost:3000

4) If the one‑command script doesn’t work, do it manually
- Start Qdrant (vector DB):
```bash
docker compose -f docker/docker-compose.yml up -d qdrant
```
- Start Ollama and pull a model:
```bash
ollama serve &
ollama pull qwen2.5:7b-instruct
```
- Start the backend (FastAPI):
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Start the frontend (Next.js):
```bash
cd frontend
npm install
npm run dev
```
- Open the app: http://localhost:3000

5) Use it
- Click “Upload” to add PDF/DOCX/TXT/MD/EPUB files
- Ask your question in the chat input
- Toggle the sources panel with the “i” icon to see which docs were used

Tips
- First run may take a minute (model pull, first build). Refresh if the UI is blank.
- If ports are busy: stop other apps using 3000/8000/6333 or reboot Docker Desktop.
- To stop everything from the one‑command run, press Ctrl+C in the Terminal windows.

## �🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker (for Qdrant)
- Ollama (local LLM): https://ollama.ai/

### 1) Clone

```bash
git clone <repository-url>
cd RAG_APP
```

### 2) Start vector database (Qdrant)

```bash
docker compose -f docker/docker-compose.yml up -d qdrant
```

### 3) Backend

```bash
cd backend
pip install -e .

# Start Ollama and pull a model (choose one)
ollama serve &
ollama pull qwen2.5:7b-instruct   # default here
# or: ollama pull llama3.1:8b

# Start FastAPI (reload for dev)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4) Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5) Open the app

- UI: http://localhost:3000
- API: http://localhost:8000

If the page doesn’t load, give it a few seconds on first run and refresh.

## ⚡ Quick Try (one command)

Runs Qdrant (Docker), Backend (FastAPI), and Frontend (Next.js) for a quick local demo:

```bash
chmod +x scripts/quick_try.sh
./scripts/quick_try.sh
```

Notes:
- Requires Docker, Python, Node, and (ideally) Ollama installed.
- Press Ctrl+C in the terminal to stop both backend and frontend.

## 🐳 Docker (Frontend + Backend + Qdrant)

Run everything in Docker for a one-command start.

```bash
docker compose -f docker/docker-compose.yml --profile full up -d
```

Services
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Qdrant: http://localhost:6333

Notes
- Ollama runs on your host at `http://localhost:11434`. Make sure it’s serving and a model is pulled:
```bash
ollama serve &
ollama pull qwen2.5:7b-instruct
```
- On macOS/Windows, containers reach your host via `host.docker.internal` (preconfigured). On Linux, you may need to map the host gateway or expose Ollama differently.

## 🧭 How To Use

- Upload documents
    - Use the Upload control in the UI to add PDF/DOCX/TXT/MD/EPUB files.
    - The status bar shows indexing progress; the Documents list updates to “indexed”.

- Ask questions
    - Type queries in the chat input. Responses render with Markdown and KaTeX (math supported: inline $a^2+b^2=c^2$ or blocks with $$...$$).

- View sources
    - Toggle the sources panel with the “i” icon in the header to see which docs the answer used.

- Model indicator
    - The header shows the active LLM model name reported by the backend.

## 🛠️ Configuration

Create `backend/.env` (values shown are sensible defaults):

```bash
# Performance profile
RAG_PROFILE=balanced   # eco|balanced|performance

# Data directory (default expands to ~/RAGApp)
RAG_DATA_DIR=~/RAGApp

# Services
QDRANT_URL=http://localhost:6333
OLLAMA_HOST=http://localhost:11434

# Models
RAG_LLM_MODEL=qwen2.5:7b-instruct  # or llama3.1:8b, etc.
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG parameters
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=200
RAG_MAX_CONTEXT_TOKENS=4000

# Debug logging
RAG_DEBUG=false
```

## 🏗️ Architecture

```
┌───────────────────┐   ┌──────────────────┐   ┌─────────────────┐
│     Next.js UI    │◄──│  FastAPI + WS    │◄──│     Qdrant      │
│  (React/TypeScript)│  │   (Backend)      │   │  (Vector Store) │
└───────────────────┘   └──────────────────┘   └─────────────────┘
                     │                      │                       │
                     │                      ▼                       │
                     │             ┌─────────────────┐              │
                     │             │     Ollama      │              │
                     │             │   (Local LLM)   │              │
                     └─────────────┴─────────────────┴──────────────┘
```

### Core Components

- Frontend: Next.js (React + TypeScript)
- Backend: FastAPI + WebSocket streaming
- Vector store: Qdrant (local)
- LLM: Ollama (qwen2.5, llama3.x, etc.)
- Embeddings: Sentence Transformers (local)

## 📁 Project Structure

```
RAG_APP/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI app entry
│       ├── api_complete.py  # REST endpoints (incl. /api/status)
│       ├── ws.py            # WebSocket streaming
│       ├── models.py        # Pydantic models
│       ├── settings.py      # Config
│       ├── storage.py       # File ops (uploads, parsed)
│       ├── chunking.py      # Adaptive chunking
│       ├── embeddings.py    # Local embeddings
│       ├── qdrant_index.py  # Vector store ops
│       ├── retrieval.py     # Retrieval logic
│       └── llm.py           # LLM service
├── frontend/
│   └── src/
│       ├── components/      # UI components
│       ├── hooks/           # React Query hooks
│       ├── lib/             # API client & constants
│       └── types/           # TypeScript types
├── docker/
│   └── docker-compose.yml   # Qdrant (and optional backend) services
└── README.md
```

## � Performance Profiles

| Profile | CPU Usage | RAM Usage | Accuracy | Best For |
|--------:|-----------|-----------|----------|----------|
| Eco | Low | ~2GB | Good | Battery life, older laptops |
| Balanced | Medium | ~4GB | Better | Most users |
| Performance | High | ~8GB | Best | Powerful machines |

Set via env var:

```bash
export RAG_PROFILE=balanced
```

## 🔧 Development

### Backend

```bash
cd backend
pip install -e ".[dev]"

# Run tests
pytest

# Lint/format
black app/ tests/
isort app/ tests/
mypy app/

# Start API with auto-reload
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000

# Build
npm run build
```

## � Troubleshooting

**Qdrant connection failed**

```bash
curl http://localhost:6333/health
docker compose -f docker/docker-compose.yml restart qdrant
```

**Ollama model not found**

```bash
ollama list
ollama pull qwen2.5:7b-instruct
```

**Frontend shows timeout (~30s) or slow status**

- Ensure both services are running (http://localhost:3000 and http://localhost:8000)
- Check `/api/status`: `curl http://localhost:8000/api/status`
- Make sure Ollama is serving and `RAG_LLM_MODEL` matches a pulled model
- Status health checks are capped to ~2s; if still slow, verify Qdrant and Ollama

**Out of memory errors**

```bash
export RAG_PROFILE=eco
export RAG_MAX_CONTEXT_TOKENS=2000
```

### Logs & Data

Application data (uploads, parsed, indices, logs) lives under `~/RAGApp/` by default.
Logs are written to `~/RAGApp/logs/app.jsonl`.

## 🔒 Security & Privacy

- Local processing: All operations happen on your machine
- No external cloud calls: Works fully offline (Ollama + Qdrant local)
- Optional encryption at rest and secure deletion supported
- No telemetry or tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Commit (`git commit -m "Describe your change"`)
4. Push (`git push origin feature/my-change`)
5. Open a Pull Request

## 📄 License

MIT — see [LICENSE](LICENSE).

## 🙏 Acknowledgments

- Qdrant — Vector similarity search
- Ollama — Local LLM runtime
- FastAPI — Python web framework
- Next.js — React framework
- Sentence Transformers — Embeddings

---

Built with privacy in mind — your documents stay local.
