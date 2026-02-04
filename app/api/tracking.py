
from fastapi import APIRouter, Request, BackgroundTasks
from app.database.connection import db_instance
import logging
import time

router = APIRouter()
logger = logging.getLogger("honeypot")

def log_ip_capture(path: str, ip: str, user_agent: str):
    """
    Logs the captured IP to an active session?
    Ideally we need to associate this click with a sessionId.
    Since the link is generic, maybe we extract sessionId from query param?
    Or if we can't, we just store it in a 'honey_hits' collection.
    """
    # Try to find a recent session expecting IP? 
    # For this hackathon, let's assume valid links have ?s=session_id
    # But user said: "whatever is written after / ... will do same ip address capturing"
    
    db = db_instance.get_collection("honey_hits")
    hit = {
        "path": path,
        "ip": ip,
        "user_agent": user_agent,
        "timestamp": time.time()
    }
    db.insert_one(hit)
    logger.info(f"🕸️ HONEYPOT HIT: {ip} on {path}")

@router.get("/{full_path:path}")
async def capture_scammer(request: Request, full_path: str, background_tasks: BackgroundTasks):
    """
    Catch-all route to simulate 'receipt.pdf' or whatever.
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    
    background_tasks.add_task(log_ip_capture, full_path, client_ip, user_agent)
    
    # Return a fake PDF or generic message
    return {"message": "File is corrupted. Please try again.", "error_code": "PDF_LOAD_FAIL"}
