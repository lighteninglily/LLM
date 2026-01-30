"""Database API - RAGFlow knowledge base management"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import uuid

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schemas import (
    DatabaseConfig, DatabaseInfo, UploadRequest, 
    TransformResponse, JobStatus
)
from services.ragflow_client import ragflow_client
from services.job_manager import job_manager

router = APIRouter()


@router.get("/", response_model=List[DatabaseInfo])
async def list_databases():
    """List all RAGFlow knowledge bases"""
    try:
        databases = await ragflow_client.list_databases()
        return databases
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=DatabaseInfo)
async def create_database(config: DatabaseConfig):
    """Create a new RAGFlow knowledge base"""
    try:
        db = await ragflow_client.create_database(
            name=config.name,
            chunk_size=config.chunk_size,
            enable_kg=config.enable_kg
        )
        return db
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=TransformResponse)
async def upload_files(
    request: UploadRequest,
    background_tasks: BackgroundTasks
):
    """Upload transformed files to RAGFlow and optionally build KG"""
    if not request.files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    job_id = f"upload-{str(uuid.uuid4())[:8]}"
    job_manager.create_job(
        job_id=job_id,
        files=request.files,
        database_name=request.database_name,
        job_type="upload"
    )
    
    async def run_upload():
        try:
            job_manager.update_status(job_id, JobStatus.RUNNING)
            
            # Upload files
            for i, file_path in enumerate(request.files):
                job_manager.update_progress(
                    job_id, 
                    progress=(i / len(request.files)) * 80,
                    current_file=file_path
                )
                await ragflow_client.upload_file(request.database_name, file_path)
            
            # Parse files
            job_manager.update_progress(job_id, progress=85, current_file="Parsing...")
            await ragflow_client.parse_files(request.database_name)
            
            # Build KG if requested
            if request.build_kg:
                job_manager.update_progress(job_id, progress=90, current_file="Building KG...")
                await ragflow_client.build_kg(request.database_name)
            
            job_manager.complete_job(job_id)
        except Exception as e:
            job_manager.fail_job(job_id, str(e))
    
    background_tasks.add_task(run_upload)
    
    return TransformResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message=f"Upload started for {len(request.files)} files to {request.database_name}"
    )


@router.get("/{database_name}/status")
async def get_database_status(database_name: str):
    """Get detailed status of a knowledge base"""
    try:
        status = await ragflow_client.get_database_status(database_name)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{database_name}")
async def delete_database(database_name: str):
    """Delete a RAGFlow knowledge base"""
    try:
        await ragflow_client.delete_database(database_name)
        return {"deleted": database_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
