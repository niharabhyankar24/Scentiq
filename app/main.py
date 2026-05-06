from fastapi import FastAPI
from app.database import engine, Base

import app.models.fragrance
import app.models.note
import app.models.user
import app.models.collection
import app.models.pricing
import app.models.similarity

from app.routes.similarity import router as similarity_router
from app.routes.pricing import router as pricing_router
from app.routes.fragrance import router as fragrance_router
from app.routes.auth import router as auth_router
from app.routes.collection import router as collection_router
from app.routes.note import router as note_router
import app.models.ai_insights
from app.routes.analysis import router as analysis_router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(fragrance_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(collection_router, prefix="/api")
app.include_router(note_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(pricing_router, prefix="/api")
app.include_router(similarity_router, prefix="/api")

@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "Perfume Platform API is running"}