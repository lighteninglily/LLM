"""Transform Runner - executes transformation pipeline"""
import sys
import os
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.schemas import JobStatus
from services.job_manager import job_manager

TRANSFORM_SCRIPT = Path("/home/ryan/Documents/VSMS/ragflow_automation/transform.py")
SETUP_RAGFLOW_SCRIPT = Path("/home/ryan/Documents/VSMS/ragflow_automation/setup_ragflow.py")
VENV_PYTHON = Path("/home/ryan/Documents/VSMS/ragflow_automation/.venv/bin/python3")
OUTPUT_DIR = Path("/home/ryan/Documents/VSMS/ragflow_automation/v3_output")
CONFIG_DIR = Path("/home/ryan/Documents/VSMS/ragflow_automation/config")


async def run_transform(job_id: str):
    """Run transformation for a job"""
    job = job_manager._jobs.get(job_id)
    if not job:
        return
    
    files = job["files"]
    output_dir = job.get("output_dir") or str(OUTPUT_DIR)
    
    try:
        job_manager.update_status(job_id, JobStatus.RUNNING)
        job_manager.add_log(job_id, f"Starting transform for {len(files)} files")
        
        # Create temporary input directory with selected files
        temp_input = Path(f"/tmp/transform_input_{job_id}")
        temp_input.mkdir(exist_ok=True)
        
        # Copy/link selected files
        for file_path in files:
            src = Path(file_path)
            dst = temp_input / src.name
            if not dst.exists():
                os.symlink(src, dst)
        
        job_manager.add_log(job_id, f"Input directory: {temp_input}")
        job_manager.add_log(job_id, f"Output directory: {output_dir}")
        
        # Run transform.py
        cmd = [
            str(VENV_PYTHON),
            str(TRANSFORM_SCRIPT),
            "--input", str(temp_input),
            "--output", output_dir
        ]
        
        job_manager.add_log(job_id, f"Command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(TRANSFORM_SCRIPT.parent)
        )
        
        # Stream output
        completed = 0
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            
            line_text = line.decode().strip()
            job_manager.add_log(job_id, line_text)
            
            # Parse progress from log lines
            if "Transforming" in line_text and ".csv" in line_text:
                completed += 1
                progress = (completed / len(files)) * 100
                # Extract filename
                parts = line_text.split("Transforming ")
                if len(parts) > 1:
                    current = parts[1].split(":")[0]
                    job_manager.update_progress(
                        job_id, 
                        progress=progress,
                        current_file=current,
                        completed_files=completed
                    )
        
        await process.wait()
        
        if process.returncode == 0:
            job_manager.add_log(job_id, "Transform completed successfully")
            
            # Step 2: Upload to RAGFlow
            database_name = job.get("database_name", "client_data_kb")
            if database_name:
                job_manager.add_log(job_id, f"Starting RAGFlow upload: {database_name}")
                job_manager.update_progress(job_id, progress=80, current_file="Uploading to RAGFlow...")
                
                await run_ragflow_setup(job_id, output_dir, database_name)
            else:
                job_manager.complete_job(job_id)
        else:
            job_manager.add_log(job_id, f"Transform failed with code {process.returncode}")
            job_manager.fail_job(job_id, f"Exit code: {process.returncode}")
        
        # Cleanup temp directory
        import shutil
        shutil.rmtree(temp_input, ignore_errors=True)
        
    except Exception as e:
        job_manager.add_log(job_id, f"Error: {str(e)}")
        job_manager.fail_job(job_id, str(e))


async def run_ragflow_setup(job_id: str, output_dir: str, database_name: str):
    """Upload transformed files to RAGFlow and trigger parsing"""
    try:
        job_manager.add_log(job_id, f"Creating dataset: {database_name}")
        
        # Run setup_ragflow.py
        cmd = [
            str(VENV_PYTHON),
            str(SETUP_RAGFLOW_SCRIPT),
            "--data", output_dir,
            "--name", database_name,
            "--skip-kg"  # Skip KG for now, can be run separately
        ]
        
        job_manager.add_log(job_id, f"Command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(SETUP_RAGFLOW_SCRIPT.parent)
        )
        
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            
            line_text = line.decode().strip()
            job_manager.add_log(job_id, line_text)
            
            # Update progress based on log content
            if "Uploading" in line_text:
                job_manager.update_progress(job_id, progress=85, current_file="Uploading files...")
            elif "Parsing" in line_text:
                job_manager.update_progress(job_id, progress=90, current_file="Parsing documents...")
            elif "COMPLETE" in line_text:
                job_manager.update_progress(job_id, progress=100, current_file="Complete!")
        
        await process.wait()
        
        if process.returncode == 0:
            job_manager.add_log(job_id, f"RAGFlow setup complete: {database_name}")
            job_manager.complete_job(job_id)
        else:
            job_manager.add_log(job_id, f"RAGFlow setup failed with code {process.returncode}")
            job_manager.fail_job(job_id, f"RAGFlow setup failed: {process.returncode}")
            
    except Exception as e:
        job_manager.add_log(job_id, f"RAGFlow setup error: {str(e)}")
        job_manager.fail_job(job_id, str(e))


async def run_analysis(file_path: str) -> Dict[str, Any]:
    """Run schema analysis on a single file"""
    from pathlib import Path
    import json
    import csv
    
    path = Path(file_path)
    
    # Count records
    record_count = 0
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            record_count = sum(1 for _ in reader)
    except:
        pass
    
    # For now, return basic analysis
    # TODO: Call actual analyze_file_schema from transform.py
    return {
        "record_type": "data_record",
        "entities": ["entity1", "entity2"],
        "retrieval_sensitive_fields": [
            {"field": "date", "type": "date", "reason": "Date filtering"},
            {"field": "id", "type": "identifier", "reason": "Exact matching"}
        ],
        "record_count": record_count
    }
