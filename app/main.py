from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.connection import db_instance

# Lifespan events allow us to run code on startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    db_instance.connect()
    yield
    # --- SHUTDOWN ---
    db_instance.disconnect()

from app.api import routes
from app.api import callback
from app.api import tracking

app = FastAPI(title="Agentic Honeypot API", version="1.0.0", lifespan=lifespan)

# Include routers - Order matters! Specific routes first, catch-all last.
app.include_router(routes.router)
app.include_router(callback.router, prefix="/admin")
app.include_router(tracking.router) # Catch-all is here

@app.get("/health")
def health_check():
    return {"status": "active", "database": "connected"}