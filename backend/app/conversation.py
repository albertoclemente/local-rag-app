"""
Conversation Context Management
Handles session-based conversation history and context for follow-up questions.
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import json
from pathlib import Path

from app.models import ConversationSession, ConversationTurn
from app.diagnostics import get_logger

logger = get_logger(__name__)

class ConversationManager:
    """Manages conversation sessions and context"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        self.max_session_age_hours = 24  # Auto-cleanup after 24 hours
        self.max_turns_per_session = 50  # Limit memory usage
        
    def get_or_create_session(self, session_id: str) -> ConversationSession:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(
                session_id=session_id,
                created_at=datetime.now(),
                last_active=datetime.now()
            )
            logger.info(f"Created new conversation session: {session_id}")
        else:
            # Update last active time
            self.sessions[session_id].last_active = datetime.now()
            
        return self.sessions[session_id]
    
    def add_turn(self, session_id: str, turn_id: str, query: str, response: str, sources: List[Dict] = None):
        """Add a conversation turn to the session"""
        session = self.get_or_create_session(session_id)
        session.add_turn(turn_id, query, response, sources or [])
        
        # Limit the number of turns to prevent memory issues
        if len(session.turns) > self.max_turns_per_session:
            # Keep only the most recent turns
            session.turns = session.turns[-self.max_turns_per_session:]
        
        logger.info(f"Added turn to session {session_id}: {len(session.turns)} total turns")
    
    def get_context_for_query(self, session_id: str, max_turns: int = 5) -> str:
        """Get conversation context for LLM processing"""
        if session_id not in self.sessions:
            return ""
        
        session = self.sessions[session_id]
        return session.get_context_for_llm(max_turns)
    
    def clear_session_context(self, session_id: str) -> bool:
        """Clear conversation history for a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared context for session: {session_id}")
            return True
        return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "turn_count": len(session.turns),
            "created_at": session.created_at.isoformat(),
            "last_active": session.last_active.isoformat()
        }
    
    def get_session_turns(self, session_id: str) -> Optional[List[Dict]]:
        """Get conversation turns for a session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return [
            {
                "turn_id": turn.turn_id,
                "query": turn.query,
                "response": turn.response,
                "sources": turn.sources,
                "timestamp": turn.timestamp.isoformat()
            }
            for turn in session.turns
        ]
    
    def cleanup_old_sessions(self):
        """Remove sessions that are too old"""
        cutoff_time = datetime.now() - timedelta(hours=self.max_session_age_hours)
        old_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.last_active < cutoff_time
        ]
        
        for session_id in old_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up old session: {session_id}")
        
        if old_sessions:
            logger.info(f"Cleaned up {len(old_sessions)} old sessions")
    
    def get_all_sessions(self) -> List[Dict]:
        """Get information about all active sessions"""
        return [self.get_session_info(session_id) for session_id in self.sessions.keys()]

# Global conversation manager instance
conversation_manager = ConversationManager()

def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance"""
    return conversation_manager
