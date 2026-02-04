
from fastapi import APIRouter

router = APIRouter()

@router.post("/guvi-report")
async def guvi_callback():
    return {"status": "reported"}
