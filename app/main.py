
from fastapi import FastAPI
from app.api import routes
# from app.core.config import settings

app = FastAPI(title="Agentic Honeypot")

# Include routers
# app.include_router(routes.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Agentic Honeypot"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
