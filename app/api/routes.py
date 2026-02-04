from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel
from typing import List, Optional

from app.core.config import settings
# NOW WE IMPORT THE BRAIN SERVICE INSTEAD OF DOING IT OURSELVES
from app.agent.brain import brain_service 

router = APIRouter()

class MessageData(BaseModel):
    sender: str
    text: str
    timestamp: int

class ScamRequest(BaseModel):
    sessionId: str
    message: MessageData
    conversationHistory: Optional[List[dict]] = []
    metadata: Optional[dict] = {}

@router.post("/chat")
async def chat_endpoint(
    request: ScamRequest, 
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None) 
):
    # 1. Security
    if x_api_key != settings.GUVI_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # 2. Delegate Logic to Brain
    # The brain now handles everything: State, Scam Check, Planning, Generation, History
    agent_reply = brain_service.process_turn(request.sessionId, request.message.text)
    
    # 3. Save (Already done inside process_turn, but just ensuring no double save if legacy code existed)
    # brain_service.save_interaction(request.sessionId, incoming_text, agent_reply)

    return {
        "status": "success",
        "reply": agent_reply
    }