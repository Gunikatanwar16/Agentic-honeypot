"""
Session Manager - Updated
Added fields for GUVI callback tracking
"""

from datetime import datetime
from typing import Dict, Optional


class Session:
    """Session class with GUVI-specific fields"""
    
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.scam_detected = False
        self.confidence = 0.0
        self.scam_type = None
        self.scam_indicators = []  # New: Store detected indicators
        self.turn_count = 0
        self.created_at = datetime.now()
        self.agent = None
        self.callback_sent = False  # New: Track if final callback sent
        self.extracted_data = {
            'upi_ids': [],
            'bank_accounts': [],
            'phone_numbers': [],
            'urls': []
        }

    def get_duration(self) -> int:
        """Session duration in seconds"""
        return int((datetime.now() - self.created_at).total_seconds())


class SessionManager:
    """Manages all active sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    def create_session(self, conversation_id: str) -> Session:
        """Create new session"""
        session = Session(conversation_id)
        self.sessions[conversation_id] = session
        print(f"📌 New session created: {conversation_id}")
        return session

    def get_session(self, conversation_id: str) -> Optional[Session]:
        """Get existing session"""
        return self.sessions.get(conversation_id)

    def get_or_create_session(self, conversation_id: str) -> Session:
        """Get session or create if doesn't exist"""
        session = self.get_session(conversation_id)
        if not session:
            session = self.create_session(conversation_id)
        return session

    def delete_session(self, conversation_id: str):
        """Delete session"""
        if conversation_id in self.sessions:
            del self.sessions[conversation_id]
            print(f"🗑️  Session deleted: {conversation_id}")

    def get_all_sessions(self) -> Dict[str, Session]:
        """Get all sessions"""
        return self.sessions
    
    def get_active_count(self) -> int:
        """Count active sessions"""
        return len(self.sessions)