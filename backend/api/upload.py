"""
File Upload API - Session-only CSV/Excel analysis
Uploads are stored as temporary SQLite tables for the session.
"""

import os
import pandas as pd
from io import BytesIO, StringIO
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sqlite3
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])

# In-memory tracking of uploaded tables (session-based)
UPLOADED_TABLES: Dict[str, Dict[str, Any]] = {}

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "production.db")


class UploadResponse(BaseModel):
    success: bool
    table_name: str
    columns: List[str]
    row_count: int
    preview: List[Dict[str, Any]]
    message: str


class TableListResponse(BaseModel):
    tables: List[Dict[str, Any]]


def sanitize_table_name(filename: str) -> str:
    """Create a safe table name from filename."""
    # Remove extension and special characters
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)  # Remove multiple underscores
    name = name.strip('_').lower()
    # Add prefix and timestamp for uniqueness
    timestamp = datetime.now().strftime("%H%M%S")
    return f"upload_{name}_{timestamp}"


def infer_sqlite_type(dtype) -> str:
    """Convert pandas dtype to SQLite type."""
    dtype_str = str(dtype)
    if 'int' in dtype_str:
        return 'INTEGER'
    elif 'float' in dtype_str:
        return 'REAL'
    elif 'datetime' in dtype_str:
        return 'TEXT'  # SQLite doesn't have native datetime
    elif 'bool' in dtype_str:
        return 'INTEGER'
    else:
        return 'TEXT'


def create_temp_table(df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
    """Create a temporary table in SQLite from DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    try:
        # Drop table if exists (for re-uploads)
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # Create table with inferred schema
        columns = []
        for col in df.columns:
            safe_col = re.sub(r'[^a-zA-Z0-9_]', '_', str(col)).lower()
            sql_type = infer_sqlite_type(df[col].dtype)
            columns.append(f'"{safe_col}" {sql_type}')
        
        create_sql = f"CREATE TABLE {table_name} ({', '.join(columns)})"
        conn.execute(create_sql)
        
        # Insert data
        df.columns = [re.sub(r'[^a-zA-Z0-9_]', '_', str(col)).lower() for col in df.columns]
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        conn.commit()
        
        # Get row count
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        return {
            "success": True,
            "table_name": table_name,
            "columns": list(df.columns),
            "row_count": row_count
        }
    except Exception as e:
        logger.error(f"Failed to create temp table: {e}")
        raise
    finally:
        conn.close()


@router.post("/csv", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and create a temporary table."""
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read file contents
        contents = await file.read()
        
        # Try different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(BytesIO(contents), encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise HTTPException(status_code=400, detail="Could not decode file. Try UTF-8 encoding.")
        
        # Clean up column names
        df.columns = df.columns.str.strip()
        
        # Create table name
        table_name = sanitize_table_name(file.filename)
        
        # Create temp table
        result = create_temp_table(df, table_name)
        
        # Store metadata
        UPLOADED_TABLES[table_name] = {
            "filename": file.filename,
            "columns": result["columns"],
            "row_count": result["row_count"],
            "uploaded_at": datetime.now().isoformat()
        }
        
        # Get preview (first 5 rows)
        preview = df.head(5).to_dict(orient='records')
        
        logger.info(f"Created temp table {table_name} with {result['row_count']} rows")
        
        return UploadResponse(
            success=True,
            table_name=table_name,
            columns=result["columns"],
            row_count=result["row_count"],
            preview=preview,
            message=f"Uploaded '{file.filename}' as table '{table_name}'. You can now query it!"
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/excel", response_model=UploadResponse)
async def upload_excel(file: UploadFile = File(...)):
    """Upload an Excel file and create a temporary table."""
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel (.xlsx or .xls)")
    
    try:
        contents = await file.read()
        
        # Read Excel file
        df = pd.read_excel(BytesIO(contents))
        
        # Clean up column names
        df.columns = df.columns.str.strip()
        
        # Create table name
        table_name = sanitize_table_name(file.filename)
        
        # Create temp table
        result = create_temp_table(df, table_name)
        
        # Store metadata
        UPLOADED_TABLES[table_name] = {
            "filename": file.filename,
            "columns": result["columns"],
            "row_count": result["row_count"],
            "uploaded_at": datetime.now().isoformat()
        }
        
        # Get preview
        preview = df.head(5).to_dict(orient='records')
        
        logger.info(f"Created temp table {table_name} with {result['row_count']} rows")
        
        return UploadResponse(
            success=True,
            table_name=table_name,
            columns=result["columns"],
            row_count=result["row_count"],
            preview=preview,
            message=f"Uploaded '{file.filename}' as table '{table_name}'. You can now query it!"
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables", response_model=TableListResponse)
async def list_uploaded_tables():
    """List all uploaded tables in the current session."""
    tables = []
    for table_name, meta in UPLOADED_TABLES.items():
        tables.append({
            "table_name": table_name,
            "filename": meta["filename"],
            "columns": meta["columns"],
            "row_count": meta["row_count"],
            "uploaded_at": meta["uploaded_at"]
        })
    return TableListResponse(tables=tables)


@router.delete("/tables/{table_name}")
async def delete_uploaded_table(table_name: str):
    """Delete an uploaded table."""
    if table_name not in UPLOADED_TABLES:
        raise HTTPException(status_code=404, detail="Table not found")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        conn.close()
        
        del UPLOADED_TABLES[table_name]
        
        return {"success": True, "message": f"Table '{table_name}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_uploaded_tables_schema() -> str:
    """Get schema info for uploaded tables (used by SQL agent)."""
    if not UPLOADED_TABLES:
        return ""
    
    lines = ["\n=== UPLOADED TABLES (Session) ===\n"]
    for table_name, meta in UPLOADED_TABLES.items():
        lines.append(f"{table_name} ({meta['row_count']} rows) - from '{meta['filename']}'")
        lines.append(f"   Columns: {', '.join(meta['columns'])}")
        lines.append("")
    
    return "\n".join(lines)
