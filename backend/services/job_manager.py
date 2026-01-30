"""Job Manager - tracks background job status and logs"""
from typing import Dict, List, Optional
from datetime import datetime
from threading import Lock
import os

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schemas import JobStatus, JobInfo


class JobManager:
    def __init__(self):
        self._jobs: Dict[str, dict] = {}
        self._logs: Dict[str, List[str]] = {}
        self._lock = Lock()
        self._log_dir = "/home/ryan/Documents/VSMS/ragflow_automation/logs"
    
    def create_job(
        self, 
        job_id: str, 
        files: List[str],
        output_dir: Optional[str] = None,
        database_name: Optional[str] = None,
        enable_kg: bool = True,
        job_type: str = "transform"
    ):
        """Create a new job"""
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": JobStatus.PENDING,
                "progress": 0.0,
                "current_file": None,
                "total_files": len(files),
                "completed_files": 0,
                "files": files,
                "output_dir": output_dir,
                "database_name": database_name,
                "enable_kg": enable_kg,
                "job_type": job_type,
                "started_at": None,
                "completed_at": None,
                "error": None
            }
            self._logs[job_id] = []
    
    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get job info"""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                return JobInfo(**{k: v for k, v in job.items() if k in JobInfo.model_fields})
            return None
    
    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 20) -> List[JobInfo]:
        """List jobs, optionally filtered by status"""
        with self._lock:
            jobs = list(self._jobs.values())
            if status:
                jobs = [j for j in jobs if j["status"] == status]
            jobs.sort(key=lambda x: x.get("started_at") or datetime.min, reverse=True)
            return [
                JobInfo(**{k: v for k, v in j.items() if k in JobInfo.model_fields})
                for j in jobs[:limit]
            ]
    
    def update_status(self, job_id: str, status: JobStatus):
        """Update job status"""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = status
                if status == JobStatus.RUNNING and not self._jobs[job_id]["started_at"]:
                    self._jobs[job_id]["started_at"] = datetime.now()
    
    def update_progress(
        self, 
        job_id: str, 
        progress: float = None,
        current_file: str = None,
        completed_files: int = None
    ):
        """Update job progress"""
        with self._lock:
            if job_id in self._jobs:
                if progress is not None:
                    self._jobs[job_id]["progress"] = progress
                if current_file is not None:
                    self._jobs[job_id]["current_file"] = current_file
                if completed_files is not None:
                    self._jobs[job_id]["completed_files"] = completed_files
    
    def add_log(self, job_id: str, message: str):
        """Add a log message"""
        with self._lock:
            if job_id in self._logs:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self._logs[job_id].append(f"[{timestamp}] {message}")
    
    def get_logs(self, job_id: str, offset: int = 0, limit: int = 100) -> dict:
        """Get logs for a job"""
        with self._lock:
            logs = self._logs.get(job_id, [])
            total = len(logs)
            lines = logs[offset:offset + limit]
            return {
                "lines": lines,
                "has_more": offset + limit < total
            }
    
    def complete_job(self, job_id: str):
        """Mark job as completed"""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = JobStatus.COMPLETED
                self._jobs[job_id]["progress"] = 100.0
                self._jobs[job_id]["completed_at"] = datetime.now()
    
    def fail_job(self, job_id: str, error: str):
        """Mark job as failed"""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = JobStatus.FAILED
                self._jobs[job_id]["error"] = error
                self._jobs[job_id]["completed_at"] = datetime.now()
    
    def cancel_job(self, job_id: str):
        """Cancel a job"""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = JobStatus.CANCELLED
                self._jobs[job_id]["completed_at"] = datetime.now()
    
    def delete_job(self, job_id: str):
        """Delete a job from history"""
        with self._lock:
            self._jobs.pop(job_id, None)
            self._logs.pop(job_id, None)


# Singleton instance
job_manager = JobManager()
