"""
Hybrid API endpoint - Routes queries to SQL or RAG based on intent
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import logging
import yaml
from pathlib import Path

from services.sql_agent import query_with_sql, format_sql_response, classify_query
from services.database import get_schema_info

logger = logging.getLogger(__name__)

# vLLM endpoint for RAG answer generation
VLLM_ENDPOINT = "http://localhost:8000/v1/chat/completions"
MODEL_NAME = "Qwen/Qwen2.5-14B-Instruct-AWQ"

router = APIRouter(prefix="/api/hybrid", tags=["hybrid"])

# Load RAGFlow settings
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "settings.yaml"


def get_ragflow_config():
    """Load RAGFlow configuration."""
    try:
        with open(CONFIG_PATH) as f:
            settings = yaml.safe_load(f)
        return settings.get("ragflow", {})
    except:
        return {}


class QueryRequest(BaseModel):
    question: str
    chat_id: Optional[str] = None
    conversation_id: Optional[str] = None
    force_sql: bool = False
    force_rag: bool = False


class QueryResponse(BaseModel):
    answer: str
    source: str  # "sql" or "rag"
    sql_query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    rag_sources: Optional[List[str]] = None
    error: Optional[str] = None


@router.post("/query", response_model=QueryResponse)
async def hybrid_query(request: QueryRequest):
    """
    Hybrid query endpoint - routes to SQL for data queries, RAG for knowledge queries.
    """
    question = request.question.strip()
    
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    # Determine query type
    if request.force_sql:
        query_type = "sql"
    elif request.force_rag:
        query_type = "rag"
    else:
        query_type = classify_query(question)
    
    logger.info(f"Query classified as: {query_type} - '{question[:50]}...'")
    
    # Route to appropriate handler
    if query_type == "sql":
        return await handle_sql_query(question)
    else:
        return await handle_rag_query(question, request.chat_id, request.conversation_id)


async def handle_sql_query(question: str) -> QueryResponse:
    """Handle SQL-based data query."""
    try:
        # Generate and execute SQL
        sql_result = await query_with_sql(question)
        
        # Check if we should fallback to RAG
        if sql_result.get("use_rag"):
            logger.info("SQL agent suggested RAG fallback")
            return await handle_rag_query(question, None, None)
        
        if not sql_result["success"]:
            # Try RAG as fallback
            logger.warning(f"SQL query failed: {sql_result['error']}, trying RAG")
            return await handle_rag_query(question, None, None)
        
        # Format the response
        answer = await format_sql_response(question, sql_result)
        
        if not answer:
            answer = f"Found {sql_result['row_count']} results."
        
        return QueryResponse(
            answer=answer,
            source="sql",
            sql_query=sql_result["sql"],
            data=sql_result["results"][:100],  # Limit data in response
            row_count=sql_result["row_count"],
            error=None
        )
        
    except Exception as e:
        logger.error(f"SQL query handler error: {e}")
        # Fallback to RAG
        return await handle_rag_query(question, None, None)


async def handle_rag_query(
    question: str, 
    chat_id: Optional[str], 
    conversation_id: Optional[str]
) -> QueryResponse:
    """Handle RAG-based knowledge query via RAGFlow chat completions."""
    config = get_ragflow_config()
    
    if not config.get("endpoint") or not config.get("api_key"):
        return QueryResponse(
            answer="RAGFlow is not configured. Please set up RAGFlow credentials.",
            source="rag",
            error="ragflow_not_configured"
        )
    
    endpoint = config["endpoint"]
    api_key = config["api_key"]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # Use Jennmar TEST LLM chat (connected to Company Docs dataset)
    if not chat_id:
        chat_id = "f74df11afb1a11f0a189dac365dd66f0"
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Create session
            if not conversation_id:
                conv_resp = await client.post(
                    f"{endpoint}/api/v1/chats/{chat_id}/sessions",
                    headers=headers,
                    json={"name": "Hybrid Query Session"}
                )
                if conv_resp.status_code == 200:
                    conv_data = conv_resp.json().get("data", {})
                    conversation_id = conv_data.get("id")
            
            if not conversation_id:
                return QueryResponse(
                    answer="Failed to create RAGFlow conversation.",
                    source="rag",
                    error="conversation_creation_failed"
                )
            
            # Send message to RAGFlow
            msg_resp = await client.post(
                f"{endpoint}/api/v1/chats/{chat_id}/completions",
                headers=headers,
                json={
                    "question": question,
                    "session_id": conversation_id,
                    "stream": False
                }
            )
            
            if msg_resp.status_code != 200:
                return QueryResponse(
                    answer=f"RAGFlow error: {msg_resp.text}",
                    source="rag",
                    error="ragflow_request_failed"
                )
            
            result = msg_resp.json()
            answer = result.get("data", {}).get("answer", "No response from RAGFlow")
            
            # Extract source references
            sources = []
            for ref in result.get("data", {}).get("reference", {}).get("chunks", []):
                if ref.get("document_name"):
                    sources.append(ref["document_name"])
            
            return QueryResponse(
                answer=answer,
                source="rag",
                rag_sources=list(set(sources))[:10],
                error=None
            )
            
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        return QueryResponse(
            answer=f"Error processing RAG query: {str(e)}",
            source="rag",
            error=str(e)
        )


@router.get("/schema")
async def get_database_schema():
    """Get database schema information."""
    try:
        schema = get_schema_info()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for hybrid API."""
    return {
        "status": "healthy",
        "sql_available": True,
        "rag_available": bool(get_ragflow_config().get("endpoint"))
    }
