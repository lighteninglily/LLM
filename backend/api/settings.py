"""RAGFlow settings API for toggling chat configuration."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["Settings"])

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
CHAT_ID = "aef57674fce811f0bdec2271202a6525"  # Company Handbook Chat


def get_ragflow_config():
    """Load RAGFlow configuration."""
    with open(CONFIG_PATH) as f:
        settings = yaml.safe_load(f)
    return settings.get("ragflow", {})


class RAGSettings(BaseModel):
    multi_turn_optimization: Optional[bool] = None
    reasoning: Optional[bool] = None
    use_knowledge_graph: Optional[bool] = None
    top_n: Optional[int] = None
    similarity_threshold: Optional[float] = None
    rerank_model: Optional[str] = None


class DatasetInfo(BaseModel):
    name: str
    chunk_count: int
    doc_count: int


class SQLDatabaseInfo(BaseModel):
    path: str
    tables: list[str]
    total_records: int


class RAGSettingsResponse(BaseModel):
    multi_turn_optimization: bool
    reasoning: bool
    use_knowledge_graph: bool
    top_n: int
    similarity_threshold: float
    rerank_model: str
    chat_name: str
    dataset_count: int
    rag_datasets: list[DatasetInfo]
    sql_database: SQLDatabaseInfo


def get_sql_database_info() -> SQLDatabaseInfo:
    """Get SQL database info."""
    import sqlite3
    db_path = Path(__file__).parent.parent.parent / "data" / "production.db"
    
    if not db_path.exists():
        return SQLDatabaseInfo(path=str(db_path), tables=[], total_records=0)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Get total records
    total = 0
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        total += cursor.fetchone()[0]
    
    conn.close()
    return SQLDatabaseInfo(path=str(db_path), tables=tables, total_records=total)


@router.get("/rag", response_model=RAGSettingsResponse)
async def get_rag_settings():
    """Get current RAGFlow chat settings."""
    config = get_ragflow_config()
    endpoint = config.get("endpoint")
    api_key = config.get("api_key")
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Get SQL database info
    sql_info = get_sql_database_info()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{endpoint}/api/v1/chats", headers=headers)
        
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch RAGFlow settings")
        
        chats = resp.json().get("data", [])
        for chat in chats:
            if chat.get("id") == CHAT_ID:
                prompt = chat.get("prompt", {})
                datasets = chat.get("datasets", [])
                
                # Build dataset info list
                rag_datasets = [
                    DatasetInfo(
                        name=ds.get("name", "Unknown"),
                        chunk_count=ds.get("chunk_num", 0),
                        doc_count=ds.get("doc_num", 0)
                    )
                    for ds in datasets
                ]
                
                return RAGSettingsResponse(
                    multi_turn_optimization=prompt.get("refine_multiturn", False),
                    reasoning=prompt.get("reasoning", False),
                    use_knowledge_graph=prompt.get("use_kg", False),
                    top_n=prompt.get("top_n", 6),
                    similarity_threshold=prompt.get("similarity_threshold", 0.2),
                    rerank_model=prompt.get("rerank_model", ""),
                    chat_name=chat.get("name", "Unknown"),
                    dataset_count=len(datasets),
                    rag_datasets=rag_datasets,
                    sql_database=sql_info
                )
        
        raise HTTPException(status_code=404, detail="Chat assistant not found")


COMPANY_DOCS_ID = "89c9c44ef51611f08f6d02bb11ac839c"


class TableInfo(BaseModel):
    name: str
    record_count: int
    columns: list[str]
    sample_values: dict[str, list[str]]


class DataOverview(BaseModel):
    sql_tables: list[TableInfo]
    sql_total_records: int
    rag_datasets: list[DatasetInfo]
    rag_total_chunks: int


@router.get("/data-overview", response_model=DataOverview)
async def get_data_overview():
    """Get overview of all available data sources."""
    import sqlite3
    db_path = Path(__file__).parent.parent.parent / "data" / "production.db"
    
    sql_tables = []
    sql_total = 0
    
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get tables (excluding sqlite internals)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            sql_total += count
            
            # Get columns
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Get sample distinct values for key columns
            sample_values = {}
            for col in columns[:5]:  # First 5 columns
                try:
                    cursor.execute(f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL LIMIT 5")
                    values = [str(row[0]) for row in cursor.fetchall()]
                    if values:
                        sample_values[col] = values
                except:
                    pass
            
            sql_tables.append(TableInfo(
                name=table,
                record_count=count,
                columns=columns,
                sample_values=sample_values
            ))
        
        conn.close()
    
    # Get RAG datasets
    config = get_ragflow_config()
    endpoint = config.get("endpoint")
    api_key = config.get("api_key")
    headers = {"Authorization": f"Bearer {api_key}"}
    
    rag_datasets = []
    rag_total_chunks = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get datasets linked to our chat
        resp = await client.get(f"{endpoint}/api/v1/chats", headers=headers)
        if resp.status_code == 200:
            for chat in resp.json().get("data", []):
                if chat.get("id") == CHAT_ID:
                    for ds in chat.get("datasets", []):
                        chunks = ds.get("chunk_num", 0)
                        rag_total_chunks += chunks
                        rag_datasets.append(DatasetInfo(
                            name=ds.get("name", "Unknown"),
                            chunk_count=chunks,
                            doc_count=ds.get("doc_num", 0)
                        ))
    
    return DataOverview(
        sql_tables=sql_tables,
        sql_total_records=sql_total,
        rag_datasets=rag_datasets,
        rag_total_chunks=rag_total_chunks
    )


@router.put("/rag", response_model=RAGSettingsResponse)
async def update_rag_settings(settings: RAGSettings):
    """Update RAGFlow chat settings."""
    config = get_ragflow_config()
    endpoint = config.get("endpoint")
    api_key = config.get("api_key")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # Build prompt config update
    prompt_config = {}
    if settings.multi_turn_optimization is not None:
        prompt_config["refine_multiturn"] = settings.multi_turn_optimization
    if settings.reasoning is not None:
        prompt_config["reasoning"] = settings.reasoning
    if settings.use_knowledge_graph is not None:
        prompt_config["use_kg"] = settings.use_knowledge_graph
    if settings.top_n is not None:
        prompt_config["top_n"] = settings.top_n
    if settings.similarity_threshold is not None:
        prompt_config["similarity_threshold"] = settings.similarity_threshold
    if settings.rerank_model is not None:
        prompt_config["rerank_model"] = settings.rerank_model
    
    if not prompt_config:
        raise HTTPException(status_code=400, detail="No settings provided")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Update prompt settings AND re-link dataset to prevent unlinking
        resp = await client.put(
            f"{endpoint}/api/v1/chats/{CHAT_ID}",
            headers=headers,
            json={
                "prompt": prompt_config,
                "dataset_ids": [COMPANY_DOCS_ID]  # Always preserve dataset link
            }
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to update: {resp.text}")
        
        result = resp.json()
        if result.get("code") != 0:
            raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))
    
    # Return updated settings
    return await get_rag_settings()
