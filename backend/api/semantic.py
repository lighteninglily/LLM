"""
Semantic Layer API Endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import os
import json

from services.semantic_layer import (
    SemanticLayerGenerator,
    generate_mschema_format,
    SemanticLayer
)

router = APIRouter(prefix="/api/semantic", tags=["semantic"])

# Paths - data folder is at project root, not in backend
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "production.db")
SEMANTIC_LAYER_PATH = os.path.join(PROJECT_ROOT, "data", "semantic_layer.json")

# In-memory cache
_semantic_layer_cache: dict = None
_analysis_status: dict = {"status": "idle", "progress": 0, "message": ""}


class AnalyzeRequest(BaseModel):
    use_llm: bool = True


class AnalyzeResponse(BaseModel):
    status: str
    message: str


class SemanticLayerResponse(BaseModel):
    exists: bool
    generated_at: Optional[str] = None
    database_name: Optional[str] = None
    tables: Optional[Dict] = None
    relationships: Optional[List] = None
    glossary: Optional[Dict] = None
    mschema: Optional[str] = None


class UpdateGlossaryRequest(BaseModel):
    glossary: Dict[str, str]


class UpdateTableRequest(BaseModel):
    table_name: str
    description: Optional[str] = None
    business_terms: Optional[List[str]] = None


class UpdateColumnRequest(BaseModel):
    table_name: str
    column_name: str
    description: Optional[str] = None
    aliases: Optional[Dict[str, str]] = None
    business_terms: Optional[List[str]] = None


def load_semantic_layer() -> Optional[dict]:
    """Load semantic layer from file"""
    global _semantic_layer_cache
    
    if _semantic_layer_cache:
        return _semantic_layer_cache
    
    if os.path.exists(SEMANTIC_LAYER_PATH):
        with open(SEMANTIC_LAYER_PATH, 'r') as f:
            _semantic_layer_cache = json.load(f)
            return _semantic_layer_cache
    
    return None


def save_semantic_layer(layer: dict):
    """Save semantic layer to file"""
    global _semantic_layer_cache
    _semantic_layer_cache = layer
    
    with open(SEMANTIC_LAYER_PATH, 'w') as f:
        json.dump(layer, f, indent=2)


def run_analysis(use_llm: bool = True):
    """Background task to run semantic analysis using local Qwen LLM"""
    global _analysis_status, _semantic_layer_cache
    
    try:
        _analysis_status = {"status": "running", "progress": 10, "message": "Initializing..."}
        
        # Use local Qwen LLM via vLLM
        generator = SemanticLayerGenerator(DB_PATH, use_llm=use_llm)
        
        _analysis_status = {"status": "running", "progress": 30, "message": "Profiling database..."}
        layer = generator.generate(use_llm=use_llm)
        
        _analysis_status = {"status": "running", "progress": 80, "message": "Saving results..."}
        generator.save(layer, SEMANTIC_LAYER_PATH)
        
        # Reload cache
        _semantic_layer_cache = None
        load_semantic_layer()
        
        _analysis_status = {"status": "complete", "progress": 100, "message": "Analysis complete!"}
        
    except Exception as e:
        _analysis_status = {"status": "error", "progress": 0, "message": str(e)}


@router.get("/status")
async def get_analysis_status():
    """Get current analysis status"""
    return _analysis_status


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_database(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Start semantic layer analysis"""
    global _analysis_status
    
    if _analysis_status.get("status") == "running":
        raise HTTPException(status_code=400, detail="Analysis already in progress")
    
    _analysis_status = {"status": "starting", "progress": 0, "message": "Starting analysis..."}
    background_tasks.add_task(run_analysis, request.use_llm)
    
    return AnalyzeResponse(status="started", message="Analysis started in background")


@router.get("/layer", response_model=SemanticLayerResponse)
async def get_semantic_layer():
    """Get the current semantic layer"""
    layer = load_semantic_layer()
    
    if not layer:
        return SemanticLayerResponse(exists=False)
    
    # Generate M-Schema format for display
    mschema = ""
    try:
        # Convert dict back to object for mschema generation
        from services.semantic_layer import SemanticLayer, TableProfile, ColumnProfile, Relationship
        
        tables = {}
        for t_name, t_data in layer.get("tables", {}).items():
            columns = {}
            for c_name, c_data in t_data.get("columns", {}).items():
                columns[c_name] = ColumnProfile(
                    name=c_data.get("name", c_name),
                    data_type=c_data.get("data_type", "TEXT"),
                    description=c_data.get("description", ""),
                    sample_values=c_data.get("sample_values", []),
                    aliases=c_data.get("aliases", {}),
                    is_primary_key=c_data.get("is_primary_key", False)
                )
            
            tables[t_name] = TableProfile(
                name=t_name,
                description=t_data.get("description", ""),
                row_count=t_data.get("row_count", 0),
                columns=columns,
                time_column=t_data.get("time_column", ""),
                query_examples=t_data.get("query_examples", [])
            )
        
        relationships = []
        for r in layer.get("relationships", []):
            relationships.append(Relationship(
                from_table=r.get("from_table", ""),
                from_column=r.get("from_column", ""),
                to_table=r.get("to_table", ""),
                to_column=r.get("to_column", "")
            ))
        
        sl = SemanticLayer(
            database_name=layer.get("database_name", ""),
            tables=tables,
            relationships=relationships,
            glossary=layer.get("glossary", {})
        )
        
        mschema = generate_mschema_format(sl)
    except Exception as e:
        mschema = f"Error generating M-Schema: {e}"
    
    return SemanticLayerResponse(
        exists=True,
        generated_at=layer.get("generated_at"),
        database_name=layer.get("database_name"),
        tables=layer.get("tables"),
        relationships=layer.get("relationships"),
        glossary=layer.get("glossary"),
        mschema=mschema
    )


@router.put("/glossary")
async def update_glossary(request: UpdateGlossaryRequest):
    """Update the glossary"""
    layer = load_semantic_layer()
    
    if not layer:
        raise HTTPException(status_code=404, detail="Semantic layer not found. Run analysis first.")
    
    layer["glossary"] = request.glossary
    save_semantic_layer(layer)
    
    return {"status": "success", "message": "Glossary updated"}


@router.put("/table")
async def update_table(request: UpdateTableRequest):
    """Update table metadata"""
    layer = load_semantic_layer()
    
    if not layer:
        raise HTTPException(status_code=404, detail="Semantic layer not found")
    
    if request.table_name not in layer.get("tables", {}):
        raise HTTPException(status_code=404, detail=f"Table {request.table_name} not found")
    
    table = layer["tables"][request.table_name]
    
    if request.description is not None:
        table["description"] = request.description
    if request.business_terms is not None:
        table["business_terms"] = request.business_terms
    
    save_semantic_layer(layer)
    
    return {"status": "success", "message": f"Table {request.table_name} updated"}


@router.put("/column")
async def update_column(request: UpdateColumnRequest):
    """Update column metadata"""
    layer = load_semantic_layer()
    
    if not layer:
        raise HTTPException(status_code=404, detail="Semantic layer not found")
    
    if request.table_name not in layer.get("tables", {}):
        raise HTTPException(status_code=404, detail=f"Table {request.table_name} not found")
    
    table = layer["tables"][request.table_name]
    
    if request.column_name not in table.get("columns", {}):
        raise HTTPException(status_code=404, detail=f"Column {request.column_name} not found")
    
    column = table["columns"][request.column_name]
    
    if request.description is not None:
        column["description"] = request.description
    if request.aliases is not None:
        column["aliases"] = request.aliases
    if request.business_terms is not None:
        column["business_terms"] = request.business_terms
    
    save_semantic_layer(layer)
    
    return {"status": "success", "message": f"Column {request.column_name} updated"}


@router.get("/mschema")
async def get_mschema():
    """Get M-Schema format string for LLM prompts"""
    response = await get_semantic_layer()
    
    if not response.exists:
        raise HTTPException(status_code=404, detail="Semantic layer not found")
    
    return {"mschema": response.mschema}
