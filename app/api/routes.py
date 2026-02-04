
from fastapi import APIRouter

router = APIRouter()

@router.post("/chat")
async def chat_endpoint():
    return {"response": "Hello from the honeypot agent"}
