#!/bin/bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many documents do you have access to? List them if possible.",
    "sessionId": "test-session-123"
  }' \
  -s | python -m json.tool