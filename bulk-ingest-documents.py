#!/usr/bin/env python3
"""
Bulk Document Ingestion for AnythingLLM RAG System

This script automatically uploads and processes large numbers of documents
into AnythingLLM workspaces for RAG (Retrieval-Augmented Generation).

Usage:
    python3 bulk-ingest-documents.py --workspace "Company Data" --folder /path/to/documents
    python3 bulk-ingest-documents.py --workspace "Sales" --folder ./sales_reports --recursive
"""

import os
import sys
import time
import json
import argparse
import requests
from pathlib import Path
from typing import List, Dict, Optional

class AnythingLLMBulkIngester:
    """Bulk document ingestion client for AnythingLLM"""
    
    def __init__(self, base_url: str = "http://localhost:3001", api_key: Optional[str] = None):
        """
        Initialize the ingester
        
        Args:
            base_url: AnythingLLM server URL
            api_key: API key for authentication (optional for local)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Accept": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def get_or_create_workspace(self, workspace_name: str) -> Dict:
        """
        Get existing workspace or create new one
        
        Args:
            workspace_name: Name of the workspace
            
        Returns:
            Workspace information dictionary
        """
        # List workspaces
        response = requests.get(
            f"{self.base_url}/api/workspaces",
            headers=self.headers
        )
        
        if response.status_code == 200:
            workspaces = response.json().get("workspaces", [])
            for ws in workspaces:
                if ws.get("name") == workspace_name:
                    print(f"Found existing workspace: {workspace_name}")
                    return ws
        
        # Create new workspace
        print(f"Creating new workspace: {workspace_name}")
        response = requests.post(
            f"{self.base_url}/api/workspace/new",
            headers=self.headers,
            json={"name": workspace_name}
        )
        
        if response.status_code in [200, 201]:
            return response.json()["workspace"]
        else:
            raise Exception(f"Failed to create workspace: {response.text}")
    
    def upload_document(self, file_path: Path) -> str:
        """
        Upload a document to AnythingLLM
        
        Args:
            file_path: Path to the document
            
        Returns:
            Document location string
        """
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            response = requests.post(
                f"{self.base_url}/api/document/upload",
                headers={k: v for k, v in self.headers.items() if k != "Accept"},
                files=files
            )
        
        if response.status_code in [200, 201]:
            result = response.json()
            return result.get("location", "")
        else:
            raise Exception(f"Failed to upload {file_path.name}: {response.text}")
    
    def add_document_to_workspace(self, workspace_slug: str, doc_location: str):
        """
        Add uploaded document to workspace for processing
        
        Args:
            workspace_slug: Workspace slug/identifier
            doc_location: Document location from upload
        """
        response = requests.post(
            f"{self.base_url}/api/workspace/{workspace_slug}/update-embeddings",
            headers=self.headers,
            json={"adds": [doc_location]}
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to add document to workspace: {response.text}")
    
    def is_supported_file(self, file_path: Path) -> bool:
        """Check if file type is supported by AnythingLLM"""
        supported_extensions = {
            # Documents
            '.pdf', '.docx', '.doc', '.txt', '.md', '.rtf', '.odt',
            # Data
            '.csv', '.xlsx', '.xls', '.json', '.xml',
            # Code
            '.py', '.js', '.java', '.cpp', '.c', '.html', '.css',
            # Other
            '.log', '.yaml', '.yml', '.ini', '.conf'
        }
        return file_path.suffix.lower() in supported_extensions
    
    def collect_files(self, folder: Path, recursive: bool = False) -> List[Path]:
        """
        Collect all supported files from folder
        
        Args:
            folder: Folder to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of file paths
        """
        files = []
        
        if recursive:
            for root, dirs, filenames in os.walk(folder):
                for filename in filenames:
                    file_path = Path(root) / filename
                    if self.is_supported_file(file_path):
                        files.append(file_path)
        else:
            for file_path in folder.iterdir():
                if file_path.is_file() and self.is_supported_file(file_path):
                    files.append(file_path)
        
        return sorted(files)
    
    def bulk_ingest(self, workspace_name: str, folder: Path, 
                   recursive: bool = False, batch_size: int = 5):
        """
        Bulk ingest documents into workspace
        
        Args:
            workspace_name: Name of the workspace
            folder: Folder containing documents
            recursive: Whether to scan subdirectories
            batch_size: Number of files to process before pausing
        """
        print(f"\n{'='*60}")
        print(f"Bulk Document Ingestion")
        print(f"{'='*60}\n")
        
        # Get or create workspace
        workspace = self.get_or_create_workspace(workspace_name)
        workspace_slug = workspace.get("slug", workspace_name.lower().replace(" ", "-"))
        
        # Collect files
        print(f"\nScanning folder: {folder}")
        files = self.collect_files(folder, recursive)
        print(f"Found {len(files)} supported files\n")
        
        if not files:
            print("No supported files found!")
            return
        
        # Process files
        successful = 0
        failed = 0
        
        for i, file_path in enumerate(files, 1):
            try:
                print(f"[{i}/{len(files)}] Processing: {file_path.name}")
                
                # Upload file
                doc_location = self.upload_document(file_path)
                print(f"  -> Uploaded: {doc_location}")
                
                # Add to workspace
                self.add_document_to_workspace(workspace_slug, doc_location)
                print(f"  -> Added to workspace")
                
                successful += 1
                
                # Pause between batches to avoid overload
                if i % batch_size == 0 and i < len(files):
                    print(f"\n  Pausing 5 seconds before next batch...\n")
                    time.sleep(5)
                
            except Exception as e:
                print(f"  -> ERROR: {e}")
                failed += 1
                continue
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Ingestion Complete")
        print(f"{'='*60}")
        print(f"Successful: {successful}/{len(files)}")
        print(f"Failed: {failed}/{len(files)}")
        print(f"Workspace: {workspace_name}")
        print(f"\nAccess at: {self.base_url}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Bulk ingest documents into AnythingLLM RAG system"
    )
    
    parser.add_argument(
        "--workspace",
        required=True,
        help="Workspace name (will be created if doesn't exist)"
    )
    
    parser.add_argument(
        "--folder",
        required=True,
        help="Folder containing documents to ingest"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan subfolders recursively"
    )
    
    parser.add_argument(
        "--url",
        default="http://localhost:3001",
        help="AnythingLLM server URL (default: http://localhost:3001)"
    )
    
    parser.add_argument(
        "--api-key",
        help="API key for authentication (optional for local)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of files to process before pausing (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Validate folder
    folder = Path(args.folder)
    if not folder.exists():
        print(f"Error: Folder not found: {folder}")
        sys.exit(1)
    
    if not folder.is_dir():
        print(f"Error: Not a directory: {folder}")
        sys.exit(1)
    
    # Run ingestion
    try:
        ingester = AnythingLLMBulkIngester(args.url, args.api_key)
        ingester.bulk_ingest(
            args.workspace,
            folder,
            args.recursive,
            args.batch_size
        )
    except KeyboardInterrupt:
        print("\n\nIngestion cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
