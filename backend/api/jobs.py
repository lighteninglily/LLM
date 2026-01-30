"""Jobs API - monitor and manage background jobs"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schemas import JobInfo, JobLogsResponse, JobStatus
from services.job_manager import job_manager

router = APIRouter()


@router.get("/", response_model=List[JobInfo])
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    limit: int = Query(20, le=100)
):
    """List all jobs, optionally filtered by status"""
    jobs = job_manager.list_jobs(status=status, limit=limit)
    return jobs


@router.get("/{job_id}", response_model=JobInfo)
async def get_job(job_id: str):
    """Get details for a specific job"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/logs", response_model=JobLogsResponse)
async def get_job_logs(
    job_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, le=500)
):
    """Get logs for a specific job"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    logs = job_manager.get_logs(job_id, offset=offset, limit=limit)
    
    return JobLogsResponse(
        job_id=job_id,
        logs=logs["lines"],
        has_more=logs["has_more"]
    )


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Delete a completed or failed job from history"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete running job. Cancel it first."
        )
    
    job_manager.delete_job(job_id)
    return {"deleted": job_id}
