"""File browsing and management API"""
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import List, Optional
import os
import csv
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schemas import FileInfo, FileListResponse

router = APIRouter()

BASE_DIRS = [
    Path("/home/ryan/Documents/VSMS/ragflow_automation/v2_batch1"),
    Path("/home/ryan/Documents/VSMS/ragflow_automation/v2_batch2"),
    Path("/home/ryan/Documents/VSMS/ragflow_automation/v2_batch3"),
]

OUTPUT_DIR = Path("/home/ryan/Documents/VSMS/ragflow_automation/v3_output")


def count_csv_records(file_path: Path) -> Optional[int]:
    """Count records in a CSV file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            return sum(1 for _ in reader)
    except:
        return None


@router.get("/sources", response_model=FileListResponse)
async def list_source_files(
    directory: Optional[str] = Query(None, description="Specific directory to list"),
    pattern: Optional[str] = Query("*.csv", description="File pattern to match")
):
    """List available source files for transformation"""
    files = []
    
    dirs_to_scan = BASE_DIRS
    if directory:
        dirs_to_scan = [Path(directory)]
    
    for base_dir in dirs_to_scan:
        if not base_dir.exists():
            continue
            
        for file_path in base_dir.glob(pattern):
            if file_path.is_file():
                stat = file_path.stat()
                files.append(FileInfo(
                    name=file_path.name,
                    path=str(file_path),
                    size=stat.st_size,
                    records=count_csv_records(file_path),
                    modified=datetime.fromtimestamp(stat.st_mtime)
                ))
    
    files.sort(key=lambda x: x.name)
    
    return FileListResponse(
        files=files,
        total=len(files),
        directory=directory or "all"
    )


@router.get("/outputs", response_model=FileListResponse)
async def list_output_files():
    """List transformed output files"""
    files = []
    
    if OUTPUT_DIR.exists():
        for file_path in OUTPUT_DIR.glob("*.txt"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append(FileInfo(
                    name=file_path.name,
                    path=str(file_path),
                    size=stat.st_size,
                    records=None,
                    modified=datetime.fromtimestamp(stat.st_mtime)
                ))
    
    files.sort(key=lambda x: x.modified, reverse=True)
    
    return FileListResponse(
        files=files,
        total=len(files),
        directory=str(OUTPUT_DIR)
    )


@router.get("/preview/{file_path:path}")
async def preview_file(file_path: str, lines: int = Query(50, le=200)):
    """Preview file contents"""
    path = Path(file_path)
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = []
            for i, line in enumerate(f):
                if i >= lines:
                    break
                content.append(line.rstrip())
        
        return {
            "file": path.name,
            "path": str(path),
            "lines": content,
            "total_lines": sum(1 for _ in open(path, 'r', encoding='utf-8'))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/directories")
async def list_directories():
    """List available source directories"""
    dirs = []
    for d in BASE_DIRS:
        if d.exists():
            file_count = len(list(d.glob("*.csv")))
            dirs.append({
                "path": str(d),
                "name": d.name,
                "file_count": file_count
            })
    return {"directories": dirs}


@router.get("/browse")
async def browse_directory(path: str = Query("/home", description="Directory path to browse")):
    """Browse a directory like a file explorer"""
    target = Path(path)
    
    if not target.exists():
        raise HTTPException(status_code=404, detail="Directory not found")
    
    if not target.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")
    
    items = []
    
    try:
        for item in sorted(target.iterdir()):
            try:
                if item.name.startswith('.'):
                    continue
                    
                if item.is_dir():
                    # Count CSV files in subdirectory
                    try:
                        csv_count = len(list(item.glob("*.csv")))
                    except:
                        csv_count = 0
                    items.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "directory",
                        "csv_count": csv_count
                    })
                elif item.suffix.lower() == '.csv':
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "file",
                        "size": stat.st_size,
                        "records": count_csv_records(item)
                    })
            except PermissionError:
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Sort: directories first, then files
    items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
    
    return {
        "current_path": str(target),
        "parent_path": str(target.parent) if target.parent != target else None,
        "items": items
    }
