# Local RAG WebApp

A **completely local** Retrieval-Augmented Generation (RAG) web application for document Q&A. Upload your documents, ask questions, and get accurate answers—all without any cloud dependencies.

## ✨ Features

- **🔒 100% Local**: No cloud APIs, no data leaves your machine
- **📄 Multi-format Support**: PDF, DOCX, TXT, MD, EPUB documents
- **🧠 Intelligent Processing**: Adaptive chunking and dynamic-k retrieval
- **⚡ Real-time Streaming**: Live token streaming with animated indicators
- **🎯 Accurate Citations**: See exactly which documents informed each answer
- **🔧 Performance Profiles**: Eco/Balanced/Performance modes for your hardware
- **🎨 Modern UI**: React + TypeScript frontend with accessibility support

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **Node.js 18+** 
- **Docker** (for Qdrant vector database)
- **Ollama** (for local LLM) - [Install here](https://ollama.ai/)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd RAG_APP
```

### 2. Start Vector Database

```bash
cd docker
docker-compose up qdrant -d
```

### 3. Setup Backend

```bash
cd backend
pip install -e .

# Start Ollama and pull a model
ollama serve &
ollama pull llama3.2:3b

# Start the backend
python -m app.main
```

### 4. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Access the Application

Open your browser to **http://localhost:5173** (Vite dev server) or **http://localhost:8000** (production build).

## 📊 Performance Profiles

Choose the profile that matches your hardware:

| Profile | CPU Usage | RAM Usage | Accuracy | Best For |
|---------|-----------|-----------|----------|----------|
| **Eco** | Low | ~2GB | Good | Battery life, older laptops |
| **Balanced** | Medium | ~4GB | Better | Most users, daily use |
| **Performance** | High | ~8GB | Best | Powerful machines, accuracy-critical |

Set via environment variable:
```bash
export RAG_PROFILE=balanced  # eco|balanced|performance
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │◄──►│  FastAPI + WS   │◄──►│    Qdrant       │
│   (Frontend)    │    │   (Backend)     │    │ (Vector Store)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │     Ollama      │              │
         │              │  (Local LLM)    │              │
         └──────────────┴─────────────────┴──────────────┘
                        Local Processing Only
```

### Core Components

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: Python FastAPI + WebSocket streaming
- **Vector Store**: Qdrant (local) with payload filters
- **LLM**: Ollama integration (llama3.2, qwen2.5, etc.)
- **Embeddings**: Local sentence-transformers models

## 📁 Project Structure

```
RAG_APP/
├── docs/                    # Specifications (URD, SRS, HLD, LLD, UI Spec)
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI application
│   │   ├── api.py          # REST endpoints
│   │   ├── ws.py           # WebSocket streaming
│   │   ├── models.py       # Pydantic data models
│   │   ├── settings.py     # Configuration management
│   │   ├── storage.py      # File operations
│   │   ├── parsing.py      # Document text extraction
│   │   ├── chunking.py     # Adaptive chunking
│   │   ├── embeddings.py   # Local embeddings
│   │   ├── qdrant_index.py # Vector store operations
│   │   ├── retrieval.py    # RAG + dynamic-k
│   │   ├── llm.py          # LLM inference
│   │   └── diagnostics.py  # Logging & monitoring
│   └── tests/
├── frontend/                # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── lib/            # API clients
│   │   └── types.ts        # TypeScript types
│   └── package.json
├── docker/
│   └── docker-compose.yml  # Qdrant service
└── README.md
```

## 🛠️ Configuration

Create a `.env` file in the backend directory:

```bash
# Performance profile
RAG_PROFILE=balanced

# Data directory (default: ~/RAGApp)
RAG_DATA_DIR=~/RAGApp

# Services
QDRANT_URL=http://localhost:6333
OLLAMA_HOST=http://localhost:11434

# Models
RAG_LLM_MODEL=llama3.2:3b
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG parameters
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=200
RAG_MAX_CONTEXT_TOKENS=4000

# Optional: Enable debug logging
RAG_DEBUG=false
```

## 🧪 Advanced Features

### Adaptive Chunking
Documents are automatically chunked with optimal size (500-1350 tokens) based on:
- Content density and structure
- Presence of headings and tables
- Document type and length

### Dynamic-k Retrieval
The system automatically determines how many chunks to retrieve (3-10) based on:
- Query complexity and scope
- Marginal relevance scores
- Context budget constraints

### Real-time Streaming
Responses stream token-by-token via WebSocket with:
- Animated typing indicators
- Inline citation insertion
- Accessibility support (screen readers)

## 🔧 Development

### Backend Development
```bash
cd backend

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black app/ tests/
isort app/ tests/
mypy app/

# Start with auto-reload
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

## 🔒 Security & Privacy

- **Local Processing**: All operations happen on your machine
- **No Network Calls**: Application works completely offline
- **Encrypted Storage**: Optional document encryption at rest
- **Secure Deletion**: Overwrite files before deletion
- **No Telemetry**: Zero data collection or tracking

## 📊 Resource Usage

Typical usage on a modern laptop:

| Operation | CPU | RAM | Time |
|-----------|-----|-----|------|
| Document Upload (10MB PDF) | 30% | +500MB | 15s |
| Embedding Generation | 60% | +200MB | 5s |
| Query Processing | 45% | +300MB | 2s |
| LLM Response (100 tokens) | 40% | +400MB | 8s |

## 🐛 Troubleshooting

### Common Issues

**Qdrant connection failed**
```bash
# Check if Qdrant is running
curl http://localhost:6333/health

# Restart Qdrant
docker-compose -f docker/docker-compose.yml restart qdrant
```

**Ollama model not found**
```bash
# List available models
ollama list

# Pull required model
ollama pull llama3.2:3b
```

**Out of memory errors**
```bash
# Switch to Eco profile
export RAG_PROFILE=eco

# Or reduce context budget
export RAG_MAX_CONTEXT_TOKENS=2000
```

**Slow response times**
- Check system resources with `htop` or Task Manager
- Switch to Performance profile if you have >8GB RAM
- Consider using a smaller LLM model

### Logs

Application logs are stored in `~/RAGApp/logs/app.jsonl` in structured JSON format.

Enable debug logging:
```bash
export RAG_DEBUG=true
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Qdrant](https://qdrant.tech/) - Vector similarity search engine
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - Frontend framework
- [Sentence Transformers](https://www.sbert.net/) - State-of-the-art embeddings

---

**Built with ❤️ for privacy-conscious users who want to keep their documents local.**
