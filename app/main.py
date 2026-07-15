"""
Main FastAPI application entry point.
Configures middleware, rate limiting, and registers all routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import engine, Base

import app.models.fragrance
import app.models.note
import app.models.user
import app.models.collection
import app.models.ai_insights
import app.models.pricing
import app.models.similarity

from app.routes.fragrance import router as fragrance_router
from app.routes.auth import router as auth_router
from app.routes.collection import router as collection_router
from app.routes.analysis import router as analysis_router
from app.routes.pricing import router as pricing_router
from app.routes.similarity import router as similarity_router
from app.routes.note import router as note_router
from app.routes import admin
from app.routes import search

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Scentiq API",
    description="AI-powered fragrance intelligence platform",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://scentiq-chi.vercel.app/",
        "https://scentiq-production.up.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(fragrance_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(collection_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(pricing_router, prefix="/api")
app.include_router(similarity_router, prefix="/api")
app.include_router(note_router, prefix="/api")
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(
    search.router,
    prefix="/api/search",
    tags=["search"]
)

@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "Scentiq API is running"}