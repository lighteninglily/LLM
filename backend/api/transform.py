"""Transform API - handles file transformation jobs"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pathlib import Path
from typing import List
import uuid
import asyncio

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schemas import (
    TransformRequest, TransformResponse, AnalysisResult, JobStatus
)
from services.job_manager import job_manager
from services.transform_runner import run_transform, run_analysis

router = APIRouter()


@router.post("/start", response_model=TransformResponse)
async def start_transform(
    request: TransformRequest,
    background_tasks: BackgroundTasks
):
    """Start a transformation job for selected files"""
    if not request.files:
        raise HTTPException(status_code=400, detail="No files selected")
    
    # Validate files exist
    for file_path in request.files:
        if not Path(file_path).exists():
            raise HTTPException(
                status_code=404, 
                detail=f"File not found: {file_path}"
            )
    
    # Create job
    job_id = str(uuid.uuid4())[:8]
    job_manager.create_job(
        job_id=job_id,
        files=request.files,
        output_dir=request.output_dir,
        database_name=request.database_name,
        enable_kg=request.enable_kg
    )
    
    # Run in background
    background_tasks.add_task(run_transform, job_id)
    
    return TransformResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message=f"Transform job started for {len(request.files)} files"
    )


@router.post("/analyze", response_model=List[AnalysisResult])
async def analyze_files(files: List[str]):
    """Analyze files without transforming - preview schema analysis"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    for file_path in files[:5]:  # Limit to 5 files for preview
        path = Path(file_path)
        if not path.exists():
            continue
        
        try:
            analysis = await run_analysis(file_path)
            results.append(AnalysisResult(
                file=path.name,
                record_type=analysis.get("record_type", "unknown"),
                entities=analysis.get("entities", []),
                retrieval_sensitive_fields=analysis.get("retrieval_sensitive_fields", []),
                record_count=analysis.get("record_count", 0)
            ))
        except Exception as e:
            results.append(AnalysisResult(
                file=path.name,
                record_type="error",
                entities=[],
                retrieval_sensitive_fields=[],
                record_count=0
            ))
    
    return results


@router.post("/cancel/{job_id}")
async def cancel_transform(job_id: str):
    """Cancel a running transformation job"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] not in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job with status: {job['status']}"
        )
    
    job_manager.cancel_job(job_id)
    return {"job_id": job_id, "status": "cancelled"}
