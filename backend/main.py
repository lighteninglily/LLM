"""
RAGFlow Automation API
FastAPI backend for file transformation and RAGFlow integration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api import files, transform, jobs, database, hybrid, settings, semantic, myob, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("🚀 RAGFlow Automation API starting...")
    yield
    print("👋 RAGFlow Automation API shutting down...")


app = FastAPI(
    title="RAGFlow Automation API",
    description="API for managing file transformations and RAGFlow knowledge bases",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(transform.router, prefix="/api/transform", tags=["Transform"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(database.router, prefix="/api/database", tags=["Database"])
app.include_router(hybrid.router, tags=["Hybrid"])
app.include_router(settings.router, tags=["Settings"])
app.include_router(semantic.router, tags=["Semantic"])
app.include_router(myob.router, tags=["MYOB"])
app.include_router(upload.router, tags=["Upload"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "ragflow-automation"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
