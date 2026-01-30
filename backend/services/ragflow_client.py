"""RAGFlow API Client"""
import httpx
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schemas import DatabaseInfo


class RAGFlowClient:
    def __init__(self):
        self._load_config()
    
    def _load_config(self):
        """Load RAGFlow settings from config"""
        config_path = Path("/home/ryan/Documents/VSMS/ragflow_automation/config/settings.yaml")
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            ragflow_config = config.get("ragflow", {})
            self.endpoint = ragflow_config.get("endpoint", "http://localhost:9380")
            self.api_key = ragflow_config.get("api_key", "")
            self.embedding_model = ragflow_config.get("embedding_model", "nomic-embed-text@Ollama")
        except Exception as e:
            print(f"Warning: Could not load RAGFlow config: {e}")
            self.endpoint = "http://localhost:9380"
            self.api_key = ""
            self.embedding_model = "nomic-embed-text@Ollama"
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def list_databases(self) -> List[DatabaseInfo]:
        """List all knowledge bases"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.endpoint}/api/v1/datasets",
                headers=self._headers(),
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            databases = []
            for db in data.get("data", []):
                databases.append(DatabaseInfo(
                    id=db.get("id", ""),
                    name=db.get("name", ""),
                    chunk_count=db.get("chunk_count", 0),
                    status=db.get("status", "unknown"),
                    created_at=datetime.fromisoformat(
                        db.get("created_at", datetime.now().isoformat())
                    )
                ))
            return databases
    
    async def create_database(
        self, 
        name: str, 
        chunk_size: int = 512,
        enable_kg: bool = True
    ) -> DatabaseInfo:
        """Create a new knowledge base"""
        async with httpx.AsyncClient() as client:
            payload = {
                "name": name,
                "embedding_model": self.embedding_model,
                "chunk_method": "naive",
                "parser_config": {
                    "chunk_token_num": chunk_size
                }
            }
            
            response = await client.post(
                f"{self.endpoint}/api/v1/datasets",
                headers=self._headers(),
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            
            return DatabaseInfo(
                id=data.get("id", ""),
                name=data.get("name", name),
                chunk_count=0,
                status="created",
                created_at=datetime.now()
            )
    
    async def upload_file(self, database_name: str, file_path: str):
        """Upload a file to a knowledge base"""
        path = Path(file_path)
        
        async with httpx.AsyncClient() as client:
            # First get database ID
            datasets = await self.list_databases()
            db = next((d for d in datasets if d.name == database_name), None)
            if not db:
                raise ValueError(f"Database not found: {database_name}")
            
            # Upload file
            with open(path, "rb") as f:
                files = {"file": (path.name, f, "text/plain")}
                response = await client.post(
                    f"{self.endpoint}/api/v1/datasets/{db.id}/documents",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files,
                    timeout=60.0
                )
                response.raise_for_status()
    
    async def parse_files(self, database_name: str):
        """Trigger file parsing for a knowledge base"""
        async with httpx.AsyncClient() as client:
            datasets = await self.list_databases()
            db = next((d for d in datasets if d.name == database_name), None)
            if not db:
                raise ValueError(f"Database not found: {database_name}")
            
            # Get documents
            response = await client.get(
                f"{self.endpoint}/api/v1/datasets/{db.id}/documents",
                headers=self._headers(),
                timeout=30.0
            )
            response.raise_for_status()
            docs = response.json().get("data", [])
            
            # Parse each unparsed document
            doc_ids = [d["id"] for d in docs if d.get("status") != "parsed"]
            if doc_ids:
                response = await client.post(
                    f"{self.endpoint}/api/v1/datasets/{db.id}/documents/parse",
                    headers=self._headers(),
                    json={"document_ids": doc_ids},
                    timeout=300.0
                )
                response.raise_for_status()
    
    async def build_kg(self, database_name: str):
        """Build knowledge graph for a knowledge base"""
        # KG building is typically triggered through the parse process
        # or separate endpoint depending on RAGFlow version
        pass
    
    async def get_database_status(self, database_name: str) -> Dict[str, Any]:
        """Get detailed status of a knowledge base"""
        async with httpx.AsyncClient() as client:
            datasets = await self.list_databases()
            db = next((d for d in datasets if d.name == database_name), None)
            if not db:
                raise ValueError(f"Database not found: {database_name}")
            
            # Get documents status
            response = await client.get(
                f"{self.endpoint}/api/v1/datasets/{db.id}/documents",
                headers=self._headers(),
                timeout=30.0
            )
            response.raise_for_status()
            docs = response.json().get("data", [])
            
            return {
                "id": db.id,
                "name": db.name,
                "chunk_count": db.chunk_count,
                "document_count": len(docs),
                "documents": [
                    {
                        "name": d.get("name"),
                        "status": d.get("status"),
                        "chunk_count": d.get("chunk_count", 0)
                    }
                    for d in docs
                ]
            }
    
    async def delete_database(self, database_name: str):
        """Delete a knowledge base"""
        async with httpx.AsyncClient() as client:
            datasets = await self.list_databases()
            db = next((d for d in datasets if d.name == database_name), None)
            if not db:
                raise ValueError(f"Database not found: {database_name}")
            
            response = await client.delete(
                f"{self.endpoint}/api/v1/datasets/{db.id}",
                headers=self._headers(),
                timeout=30.0
            )
            response.raise_for_status()


# Singleton instance
ragflow_client = RAGFlowClient()
