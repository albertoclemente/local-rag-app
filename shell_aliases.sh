# RAG App Shell Aliases
# Add these to your ~/.zshrc file for quick access

# Start RAG App (both backend and frontend)
alias rag-start='cd /Users/alberto/projects/RAG_APP && ./start_rag_app.sh'

# Navigate to RAG App directory
alias rag-cd='cd /Users/alberto/projects/RAG_APP'

# Start backend only
alias rag-backend='cd /Users/alberto/projects/RAG_APP/backend && ./venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000'

# Start frontend only
alias rag-frontend='cd /Users/alberto/projects/RAG_APP/frontend && npm run dev'

# Open RAG App in browser
alias rag-open='open http://localhost:3000'

# View logs
alias rag-logs-backend='tail -f /tmp/rag_backend.log'
alias rag-logs-frontend='tail -f /tmp/rag_frontend.log'

# Categorize documents
alias rag-categorize='cd /Users/alberto/projects/RAG_APP/backend && ./venv/bin/python categorize_existing_docs.py'

# Run tests
alias rag-test='cd /Users/alberto/projects/RAG_APP/frontend && npm run test:smoke'

echo "RAG App aliases loaded! Use 'rag-start' to launch the application."
