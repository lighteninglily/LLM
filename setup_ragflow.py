#!/usr/bin/env python3
"""
RAGFlow Automation Toolkit - Step 3: Setup RAGFlow
Creates Knowledge Base, uploads files, runs parsing and KG generation.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
import yaml
from tqdm import tqdm

# Setup logging
def setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"setup_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def load_settings(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_analysis(analysis_path: Path) -> dict:
    with open(analysis_path) as f:
        return json.load(f)


class RAGFlowClient:
    """Client for RAGFlow REST API."""
    
    def __init__(self, endpoint: str, api_key: str, logger: logging.Logger):
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.logger = logger
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an API request with error handling and retries."""
        url = f"{self.endpoint}{path}"
        
        for attempt in range(3):
            try:
                if "headers" not in kwargs:
                    kwargs["headers"] = self.headers
                else:
                    kwargs["headers"].update(self.headers)
                
                response = requests.request(method, url, timeout=60, **kwargs)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"API returned {response.status_code}: {response.text[:200]}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"API request failed (attempt {attempt+1}): {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise
        
        return {}
    
    def test_connection(self) -> bool:
        """Test API connection and authentication."""
        try:
            result = self._request("GET", "/api/v1/datasets")
            return "data" in result or "code" in result
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def create_dataset(self, name: str, entity_types: list, embedding_model: str,
                      chunk_token_num: int = 512) -> str:
        """Create a new knowledge base."""
        payload = {
            "name": name,
            "embedding_model": embedding_model,
            "chunk_method": "naive",
            "parser_config": {
                "chunk_token_num": chunk_token_num,
                "delimiter": "\n",
                "graphrag": {
                    "use_graphrag": True,
                    "entity_types": entity_types,
                    "method": "light"
                },
                "raptor": {
                    "use_raptor": False
                }
            }
        }
        
        self.logger.info(f"Creating dataset: {name}")
        result = self._request("POST", "/api/v1/datasets", json=payload)
        
        if result.get("code") == 0 and result.get("data"):
            kb_id = result["data"]["id"]
            self.logger.info(f"Created dataset with ID: {kb_id}")
            return kb_id
        else:
            raise Exception(f"Failed to create dataset: {result}")
    
    def upload_documents(self, kb_id: str, files: list) -> list:
        """Upload documents to a knowledge base."""
        uploaded = []
        
        for file_path in tqdm(files, desc="Uploading files"):
            try:
                with open(file_path, 'rb') as f:
                    files_payload = {'file': (file_path.name, f, 'application/octet-stream')}
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    
                    response = requests.post(
                        f"{self.endpoint}/api/v1/datasets/{kb_id}/documents",
                        headers=headers,
                        files=files_payload,
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("code") == 0:
                            uploaded.append(file_path.name)
                            self.logger.info(f"Uploaded: {file_path.name}")
                        else:
                            self.logger.error(f"Upload failed for {file_path.name}: {result}")
                    else:
                        self.logger.error(f"Upload failed for {file_path.name}: {response.status_code}")
                        
            except Exception as e:
                self.logger.error(f"Failed to upload {file_path.name}: {e}")
        
        return uploaded
    
    def get_documents(self, kb_id: str) -> list:
        """Get list of documents in a knowledge base."""
        result = self._request("GET", f"/api/v1/datasets/{kb_id}/documents")
        if result.get("code") == 0:
            return result.get("data", {}).get("docs", [])
        return []
    
    def parse_documents(self, kb_id: str, doc_ids: list) -> bool:
        """Trigger document parsing."""
        payload = {"document_ids": doc_ids}
        result = self._request("POST", f"/api/v1/datasets/{kb_id}/chunks", json=payload)
        return result.get("code") == 0
    
    def wait_for_parsing(self, kb_id: str, timeout_minutes: int = 60) -> bool:
        """Wait for all documents to finish parsing."""
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        with tqdm(desc="Parsing documents", unit="check") as pbar:
            while time.time() - start_time < timeout_seconds:
                docs = self.get_documents(kb_id)
                
                if not docs:
                    time.sleep(5)
                    pbar.update(1)
                    continue
                
                statuses = [d.get("run", "pending") for d in docs]
                done_count = sum(1 for s in statuses if s in ["done", "1"])
                total = len(statuses)
                
                pbar.set_postfix({"done": f"{done_count}/{total}"})
                
                if all(s in ["done", "1"] for s in statuses):
                    self.logger.info("All documents parsed successfully")
                    return True
                
                if any(s in ["fail", "error", "-1"] for s in statuses):
                    failed = [d["name"] for d in docs if d.get("run") in ["fail", "error", "-1"]]
                    self.logger.error(f"Some documents failed parsing: {failed}")
                    return False
                
                time.sleep(10)
                pbar.update(1)
        
        self.logger.error("Parsing timed out")
        return False
    
    def run_graphrag(self, kb_id: str, doc_ids: list = None) -> bool:
        """Trigger GraphRAG generation."""
        payload = {}
        if doc_ids:
            payload["document_ids"] = doc_ids
            
        result = self._request("POST", f"/api/v1/datasets/{kb_id}/graphrag", json=payload)
        return result.get("code") == 0
    
    def get_graphrag_progress(self, kb_id: str) -> dict:
        """Get GraphRAG generation progress."""
        result = self._request("GET", f"/api/v1/datasets/{kb_id}/trace_graphrag")
        if result.get("code") == 0:
            return result.get("data", {})
        return {}
    
    def wait_for_graphrag(self, kb_id: str, estimated_hours: float, 
                         timeout_multiplier: float = 1.5) -> bool:
        """Wait for GraphRAG generation to complete."""
        timeout_seconds = max(3600, int(estimated_hours * 3600 * timeout_multiplier))
        start_time = time.time()
        last_progress = -1
        stall_count = 0
        
        print(f"\nEstimated KG time: {estimated_hours:.1f} hours")
        print("Monitoring progress (Ctrl+C to run in background)...\n")
        
        while time.time() - start_time < timeout_seconds:
            try:
                progress_data = self.get_graphrag_progress(kb_id)
                progress = progress_data.get("progress", 0)
                progress_pct = progress * 100
                
                elapsed = (time.time() - start_time) / 3600
                
                if progress > 0 and progress < 1:
                    remaining = (elapsed / progress) * (1 - progress)
                    status = f"Progress: {progress_pct:.1f}% | Elapsed: {elapsed:.1f}h | Est. remaining: {remaining:.1f}h"
                elif progress >= 1:
                    status = f"Progress: {progress_pct:.1f}% | COMPLETE"
                else:
                    status = f"Progress: {progress_pct:.1f}% | Elapsed: {elapsed:.1f}h | Starting..."
                
                print(f"\r{status:<80}", end="", flush=True)
                
                if progress >= 1.0:
                    print("\n")
                    self.logger.info("GraphRAG generation complete")
                    return True
                
                # Check for stall
                if progress == last_progress:
                    stall_count += 1
                    if stall_count > 30:  # 5 minutes of no progress
                        # Check if vLLM is still processing
                        self.logger.warning("Progress appears stalled, but may still be processing large chunks")
                else:
                    stall_count = 0
                    last_progress = progress
                
                time.sleep(10)
                
            except KeyboardInterrupt:
                print("\n\nRunning in background. Check RAGFlow UI for progress.")
                return True
        
        print("\n")
        self.logger.error("GraphRAG generation timed out")
        return False
    
    def create_chat_assistant(self, name: str, kb_ids: list) -> str:
        """Create a chat assistant linked to knowledge bases."""
        payload = {
            "name": name,
            "dataset_ids": kb_ids,
            "llm": {
                "model_name": "Qwen/Qwen2.5-7B-Instruct-AWQ___OpenAI-API@OpenAI-API-Compatible",
                "temperature": 0.1,
                "top_p": 0.3,
                "max_tokens": 2048
            },
            "prompt": {
                "system": "You are a helpful assistant. Answer questions based on the provided knowledge.\n\nKnowledge:\n{knowledge}\n\nAnswer the user's question accurately based on the above knowledge.",
                "empty_response": "I don't have enough information to answer that question."
            },
            "prompt_config": {
                "use_kg": True
            }
        }
        
        self.logger.info(f"Creating chat assistant: {name}")
        result = self._request("POST", "/api/v1/chats", json=payload)
        
        if result.get("code") == 0 and result.get("data"):
            chat_id = result["data"]["id"]
            self.logger.info(f"Created chat assistant with ID: {chat_id}")
            return chat_id
        else:
            self.logger.warning(f"Chat creation response: {result}")
            return None


def setup_ragflow(data_dir: Path, name: str, analysis: dict, 
                 settings: dict, logger: logging.Logger, skip_kg: bool = False) -> dict:
    """Main setup function."""
    
    # Initialize client
    client = RAGFlowClient(
        settings["ragflow"]["endpoint"],
        settings["ragflow"]["api_key"],
        logger
    )
    
    # Test connection
    if not client.test_connection():
        raise Exception("Failed to connect to RAGFlow API")
    
    logger.info("Connected to RAGFlow API")
    
    # Get entity types from analysis
    entity_types = analysis.get("entity_types", ["organization", "person", "location", "event"])
    
    # Create dataset
    kb_id = client.create_dataset(
        name=name,
        entity_types=entity_types,
        embedding_model=settings["ragflow"]["embedding_model"],
        chunk_token_num=settings["ragflow"]["chunk_token_num"]
    )
    
    # Get files to upload
    files = list(data_dir.glob("*.txt")) + list(data_dir.glob("*.csv")) + list(data_dir.glob("*.json"))
    files = [f for f in files if f.is_file()]
    
    if not files:
        raise Exception(f"No files found in {data_dir}")
    
    logger.info(f"Found {len(files)} files to upload")
    
    # Upload documents
    uploaded = client.upload_documents(kb_id, files)
    logger.info(f"Uploaded {len(uploaded)} files")
    
    # Get document IDs
    docs = client.get_documents(kb_id)
    doc_ids = [d["id"] for d in docs]
    
    # Trigger parsing
    logger.info("Starting document parsing...")
    if not client.parse_documents(kb_id, doc_ids):
        raise Exception("Failed to trigger document parsing")
    
    # Wait for parsing
    if not client.wait_for_parsing(kb_id):
        raise Exception("Document parsing failed or timed out")
    
    result = {
        "kb_id": kb_id,
        "kb_name": name,
        "documents_uploaded": len(uploaded),
        "entity_types": entity_types
    }
    
    if skip_kg:
        logger.info("Skipping KG generation (--skip-kg flag)")
        return result
    
    # Run GraphRAG
    logger.info("Starting Knowledge Graph generation...")
    estimated_hours = analysis.get("_metadata", {}).get("estimated_kg_hours", 1)
    
    if not client.run_graphrag(kb_id):
        raise Exception("Failed to trigger GraphRAG generation")
    
    # Wait for GraphRAG
    if not client.wait_for_graphrag(kb_id, estimated_hours):
        logger.warning("GraphRAG may still be running in background")
    
    # Create chat assistant
    chat_id = client.create_chat_assistant(f"{name} Assistant", [kb_id])
    if chat_id:
        result["chat_id"] = chat_id
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Setup RAGFlow Knowledge Base with KG")
    parser.add_argument("--data", "-d", required=True, help="Data directory with files to upload")
    parser.add_argument("--name", "-n", required=True, help="Knowledge Base name")
    parser.add_argument("--config", "-c", default=None, help="Config file")
    parser.add_argument("--analysis", "-a", default=None, help="Analysis JSON file")
    parser.add_argument("--skip-kg", action="store_true", help="Skip KG generation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    data_dir = Path(args.data).resolve()
    config_file = Path(args.config) if args.config else script_dir / "config" / "settings.yaml"
    analysis_file = Path(args.analysis) if args.analysis else script_dir / "config" / "analysis_output.json"
    
    # Setup logging
    logger = setup_logging(script_dir / "logs")
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Validate inputs
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)
    
    if not analysis_file.exists():
        logger.warning(f"Analysis file not found: {analysis_file}")
        logger.warning("Using default entity types")
        analysis = {"entity_types": ["organization", "person", "location", "event"]}
    else:
        analysis = load_analysis(analysis_file)
    
    # Load settings
    settings = load_settings(config_file)
    
    # Run setup
    try:
        result = setup_ragflow(data_dir, args.name, analysis, settings, logger, args.skip_kg)
        
        # Print summary
        print("\n" + "="*60)
        print("RAGFLOW SETUP COMPLETE")
        print("="*60)
        print(f"Knowledge Base: {result['kb_name']}")
        print(f"KB ID: {result['kb_id']}")
        print(f"Documents: {result['documents_uploaded']}")
        print(f"Entity Types: {', '.join(result['entity_types'])}")
        if result.get("chat_id"):
            print(f"Chat Assistant ID: {result['chat_id']}")
        print("="*60)
        print(f"\nAccess RAGFlow UI: {settings['ragflow']['endpoint']}")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
