
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.database.connection import db_instance
from app.core.config import settings
import requests
import logging

router = APIRouter()
logger = logging.getLogger("honeypot")

GUVI_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

def submit_report(session_id: str):
    """
    Constructs the final payload and sends it to GUVI.
    """
    db = db_instance.get_collection("active_sessions")
    session = db.find_one({"_id": session_id})
    
    if not session:
        logger.error(f"Cannot report session {session_id}: Not found")
        return

    # Calculate metrics
    history = session.get("history", [])
    total_messages = len(history) * 2 # user + agent roughly
    
    # Format Intelligence (Flatten the lists)
    extracted = session.get("extracted_data", {})
    
    payload = {
        "sessionId": session_id,
        "scamDetected": session.get("scam_confirmed", False),
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": {
            "bankAccounts": extracted.get("bank_account", []),
            "upiIds": extracted.get("upi", []),
            "phishingLinks": extracted.get("url", []),
            "phoneNumbers": extracted.get("phone", []),
            "suspiciousKeywords": extracted.get("suspicious_keywords", [])
        },
        "agentNotes": f"Persona {session.get('persona_locked')} engaged scammer. Strategy state: {session.get('strategy_state', {}).get('detail_on_focus')}"
    }

    try:
        if not settings.GUVI_API_KEY:
            logger.warning("GUVI_API_KEY not set. Skipping report upload.")
            return

        response = requests.post(GUVI_URL, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"✅ Successfully reported session {session_id} to GUVI.")
    except Exception as e:
        logger.error(f"❌ Failed to report to GUVI: {e}")


@router.post("/force-report/{session_id}")
async def force_report_endpoint(session_id: str, background_tasks: BackgroundTasks):
    """
    Manually triggers the report generation for testing or admin purposes.
    """
    background_tasks.add_task(submit_report, session_id)
    return {"status": "Report submission queued"}
