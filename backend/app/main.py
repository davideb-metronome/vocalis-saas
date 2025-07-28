"""
Vocalis SaaS - FastAPI Main Application
AI Voice Generation with Metronome Billing Integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .api import auth, billing, usage, webhooks
from .core.config import settings

from fastapi.responses import StreamingResponse
import asyncio
import json
from typing import Dict, Set

# Initialize FastAPI app
app = FastAPI(
    title="Vocalis SaaS API",
    description="AI Voice Generation with Metronome Billing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend/templates")

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])
app.include_router(usage.router, prefix="/api/usage", tags=["Usage"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])

# Frontend routes
from fastapi import Request
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("pages/landing.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("pages/signup.html", {"request": request})

@app.get("/billing", response_class=HTMLResponse)
async def billing_page(request: Request):
    return templates.TemplateResponse("pages/billing.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("pages/dashboard.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "vocalis-saas"}


# Global storage for active SSE connections (use Redis in production)
active_connections: Dict[str, Set[asyncio.Queue]] = {}

@app.get("/api/events/{customer_id}")
async def customer_events(customer_id: str):
    """
    Server-Sent Events endpoint for real-time customer notifications
    """
    async def event_stream():
        # Create a queue for this connection
        queue = asyncio.Queue()
        
        # Add to active connections
        if customer_id not in active_connections:
            active_connections[customer_id] = set()
        active_connections[customer_id].add(queue)
        
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Real-time updates active'})}\n\n"
            
            # Listen for events
            while True:
                try:
                    # Wait for event with timeout to send keep-alive
                    event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event_data)}\n\n"
                except asyncio.TimeoutError:
                    # Send keep-alive ping
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                    
        except asyncio.CancelledError:
            # Connection closed
            pass
        finally:
            # Clean up connection
            if customer_id in active_connections:
                active_connections[customer_id].discard(queue)
                if not active_connections[customer_id]:
                    del active_connections[customer_id]
    
    return StreamingResponse(event_stream(), media_type="text/plain")

async def broadcast_event(customer_id: str, event_data: dict):
    """
    Broadcast an event to all active connections for a customer
    """
    if customer_id in active_connections:
        # Send to all active connections for this customer
        for queue in active_connections[customer_id]:
            try:
                await queue.put(event_data)
            except Exception as e:
                print(f"Failed to send event to queue: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
