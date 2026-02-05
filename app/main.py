"""
Main FastAPI Application - GUVI Hackathon Format
Updated to match official GUVI requirements
"""

import os
import uvicorn
import requests
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, List
from dotenv import load_dotenv
from datetime import datetime

# Import modules
from app.detection.scam_detector import ScamDetector
from app.agent.ai_agent import ConversationalAgent
from app.utils.session_manager import SessionManager

load_dotenv()

# ============================
# FastAPI App
# ============================
app = FastAPI(
    title="AI Honeypot System - GUVI Hackathon",
    description="Agentic Honeypot for Scam Detection",
    version="2.0.0"
)

# ============================
# Initialize Components
# ============================
scam_detector = ScamDetector()
session_manager = SessionManager()

# API Key
HONEYPOT_API_KEY = os.getenv("HONEYPOT_API_KEY", "honeypot-secret-2024")

# GUVI Callback URL
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"


# ============================
# Request/Response Models (GUVI Format)
# ============================
class Message(BaseModel):
    """Single message structure"""
    sender: str  # "scammer" or "user"
    text: str
    timestamp: int  # Epoch time in milliseconds

class Metadata(BaseModel):
    """Optional metadata"""
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"

class IncomingRequest(BaseModel):
    """GUVI format incoming request"""
    sessionId: str
    message: Message
    conversationHistory: Optional[List[Message]] = []
    metadata: Optional[Metadata] = None

class AgentResponse(BaseModel):
    """GUVI format response"""
    status: str  # "success" or "error"
    reply: str   # Agent's response text


# ============================
# Helper Functions
# ============================
def verify_api_key(x_api_key: str):
    """Verify API key"""
    if x_api_key != HONEYPOT_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")


def send_final_callback(session_id: str, session):
    """
    Send final results to GUVI callback endpoint
    Called when scam is confirmed and engagement is complete
    """
    try:
        # Get extracted intelligence
        intel = session.agent.get_extracted_intelligence() if session.agent else {}
        
        # Get conversation history
        history = session.agent.get_conversation_history() if session.agent else []
        
        # Count messages (only user messages)
        total_messages = len([m for m in history if m.get("role") == "user"])
        
        # Extract suspicious keywords
        suspicious_keywords = []
        for indicator in session.scam_indicators if hasattr(session, 'scam_indicators') else []:
            if isinstance(indicator, str):
                suspicious_keywords.append(indicator)
        
        # Prepare payload
        payload = {
            "sessionId": session_id,
            "scamDetected": session.scam_detected,
            "totalMessagesExchanged": total_messages,
            "extractedIntelligence": {
                "bankAccounts": intel.get('bank_accounts', []),
                "upiIds": intel.get('upi_ids', []),
                "phishingLinks": intel.get('urls', []),
                "phoneNumbers": intel.get('phone_numbers', []),
                "suspiciousKeywords": suspicious_keywords[:10]  # Top 10
            },
            "agentNotes": f"Scam type: {session.scam_type}. Confidence: {session.confidence}. Agent engaged successfully."
        }
        
        print(f"\n📤 Sending final callback to GUVI...")
        print(f"   Session: {session_id}")
        print(f"   Total Messages: {total_messages}")
        print(f"   Intelligence Items: {sum(len(v) for v in intel.values() if isinstance(v, list))}")
        
        # Send POST request to GUVI
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"   ✅ Callback successful!")
        else:
            print(f"   ⚠️  Callback returned status: {response.status_code}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"   ❌ Callback error: {e}")
        return False


def should_send_callback(session) -> bool:
    """
    Decide when to send final callback
    Criteria:
    - Scam confirmed
    - At least 3 turns exchanged
    - Some intelligence extracted
    """
    if not session.scam_detected:
        return False
    
    if session.turn_count < 3:
        return False
    
    # Check if any intelligence extracted
    if session.agent:
        intel = session.agent.get_extracted_intelligence()
        total_items = sum(len(v) for v in intel.values() if isinstance(v, list))
        if total_items > 0:
            return True
    
    # Or if conversation is long enough
    if session.turn_count >= 5:
        return True
    
    return False


# ============================
# MAIN ENDPOINT (GUVI Format)
# ============================
@app.post("/api/message", response_model=AgentResponse)
async def handle_message(
    request: IncomingRequest,
    x_api_key: str = Header(..., alias="x-api-key")
):
    """
    Main endpoint - GUVI format
    Receives scam messages and returns agent responses
    """
    # Verify API key
    verify_api_key(x_api_key)
    
    print(f"\n{'='*60}")
    print(f"📨 INCOMING MESSAGE")
    print(f"{'='*60}")
    print(f"Session: {request.sessionId}")
    print(f"Sender: {request.message.sender}")
    print(f"Text: {request.message.text[:80]}...")
    print(f"History: {len(request.conversationHistory)} previous messages")
    
    try:
        # Get or create session
        session = session_manager.get_or_create_session(request.sessionId)
        
        # FIRST MESSAGE - Detect scam
        if session.turn_count == 0:
            print(f"\n🔍 SCAM DETECTION (First Message)")
            
            detection = scam_detector.detect_scam(request.message.text)
            
            session.scam_detected = detection['is_scam']
            session.confidence = detection['confidence']
            session.scam_type = detection.get('scam_type')
            session.scam_indicators = detection.get('indicators', [])
            
            print(f"   Result: {'🚨 SCAM' if detection['is_scam'] else '✅ Safe'}")
            print(f"   Confidence: {detection['confidence']}")
            print(f"   Type: {detection.get('scam_type')}")
        
        # ENGAGE WITH AI AGENT (if scam detected)
        if session.scam_detected:
            # Create agent if not exists
            if session.agent is None:
                print(f"\n🤖 ACTIVATING AI AGENT")
                session.agent = ConversationalAgent()
            
            # Generate response
            print(f"\n💬 GENERATING RESPONSE")
            agent_reply = session.agent.generate_response(
                scammer_message=request.message.text,
                scam_type=session.scam_type or "unknown"
            )
            
            print(f"   Agent: {agent_reply}")
            
        else:
            # Not a scam - neutral response
            agent_reply = "I'm sorry, I don't understand. Could you please clarify?"
        
        # Increment turn counter
        session.turn_count += 1
        
        # Check if we should send final callback
        if should_send_callback(session):
            print(f"\n📊 ENGAGEMENT COMPLETE - Sending callback...")
            callback_sent = send_final_callback(request.sessionId, session)
            
            if callback_sent:
                # Mark session as completed
                session.callback_sent = True
        
        # Return GUVI format response
        print(f"\n✅ RESPONSE READY")
        print(f"{'='*60}\n")
        
        return AgentResponse(
            status="success",
            reply=agent_reply
        )
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================
# Additional Endpoints (For Testing)
# ============================
@app.get("/api/session/{session_id}")
async def get_session_info(
    session_id: str,
    x_api_key: str = Header(..., alias="x-api-key")
):
    """Get session details (for testing/debugging)"""
    verify_api_key(x_api_key)
    
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "sessionId": session_id,
        "scamDetected": session.scam_detected,
        "confidence": session.confidence,
        "scamType": session.scam_type,
        "turnCount": session.turn_count,
        "callbackSent": getattr(session, 'callback_sent', False),
        "extractedIntelligence": session.agent.get_extracted_intelligence() if session.agent else {},
        "conversationHistory": session.agent.get_conversation_history() if session.agent else []
    }


@app.post("/api/test-callback")
async def test_callback(
    session_id: str,
    x_api_key: str = Header(..., alias="x-api-key")
):
    """Manually trigger callback (for testing)"""
    verify_api_key(x_api_key)
    
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    success = send_final_callback(session_id, session)
    
    return {
        "status": "success" if success else "failed",
        "message": "Callback sent to GUVI endpoint"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Honeypot System - GUVI Hackathon",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Honeypot System - GUVI Hackathon",
        "endpoints": {
            "main": "POST /api/message",
            "session": "GET /api/session/{id}",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }


# ============================
# Run Server
# ============================
if __name__ == "__main__":
    print("\n🚀 Starting GUVI Hackathon Honeypot Server...")
    print("📍 Server: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )