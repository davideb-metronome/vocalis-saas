"""
Vocalis SaaS - FastAPI Main Application
AI Voice Generation with Metronome Billing Integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .api import auth, billing, usage, webhooks, health
from .core.config import settings


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
app.include_router(health.router, prefix="/health", tags=["Health"]) 

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
    """
    Dashboard page - balance will be loaded by frontend JavaScript
    """
    return templates.TemplateResponse("pages/dashboard.html", {
        "request": request,
        "balance": 0  # Placeholder - real balance loaded by JavaScript
    })


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "vocalis-saas"}


# SSE endpoints are provided under the webhooks router


if __name__ == "__main__":
    # Use fully-qualified module path so uvicorn's reloader can import correctly
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
