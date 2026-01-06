#!/usr/bin/env python3
"""
Automated Workspace Setup for AnythingLLM

Pre-configure workspaces with settings, documents, and permissions
for production deployment.

Usage:
    python3 setup-workspaces.py --config workspaces.json
"""

import json
import sys
import argparse
import requests
from pathlib import Path
from typing import Dict, List

class WorkspaceConfigurator:
    """Automate workspace configuration"""
    
    def __init__(self, base_url: str = "http://localhost:3001", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.headers = {"Accept": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def create_workspace(self, config: Dict) -> Dict:
        """Create workspace with configuration"""
        name = config["name"]
        
        print(f"\nCreating workspace: {name}")
        
        # Create workspace
        response = requests.post(
            f"{self.base_url}/api/workspace/new",
            headers=self.headers,
            json={
                "name": name,
                "openAiTemp": config.get("temperature", 0.7),
                "openAiHistory": config.get("chat_history", 20),
                "similarityThreshold": config.get("similarity_threshold", 0.25),
                "topN": config.get("top_n_results", 4)
            }
        )
        
        if response.status_code not in [200, 201]:
            print(f"  ERROR: {response.text}")
            return None
        
        workspace = response.json().get("workspace", {})
        print(f"  Created: {workspace.get('slug')}")
        
        return workspace
    
    def configure_from_file(self, config_file: Path):
        """Configure workspaces from JSON file"""
        print(f"\n{'='*60}")
        print(f"Workspace Configuration")
        print(f"{'='*60}")
        
        with open(config_file) as f:
            config = json.load(f)
        
        workspaces = config.get("workspaces", [])
        print(f"\nConfiguring {len(workspaces)} workspace(s)...")
        
        for ws_config in workspaces:
            self.create_workspace(ws_config)
        
        print(f"\n{'='*60}")
        print(f"Configuration Complete")
        print(f"{'='*60}\n")


def create_example_config():
    """Create example configuration file"""
    example = {
        "workspaces": [
            {
                "name": "Company Knowledge Base",
                "description": "Internal documentation and policies",
                "temperature": 0.3,
                "chat_history": 20,
                "similarity_threshold": 0.25,
                "top_n_results": 5
            },
            {
                "name": "Sales Data Analysis",
                "description": "Sales reports and analytics",
                "temperature": 0.5,
                "chat_history": 10,
                "similarity_threshold": 0.3,
                "top_n_results": 4
            },
            {
                "name": "Customer Support",
                "description": "Customer queries and support docs",
                "temperature": 0.7,
                "chat_history": 15,
                "similarity_threshold": 0.2,
                "top_n_results": 6
            }
        ]
    }
    
    with open("workspaces.json", "w") as f:
        json.dump(example, f, indent=2)
    
    print("Created example config: workspaces.json")
    print("Edit this file and run: python3 setup-workspaces.py --config workspaces.json")


def main():
    parser = argparse.ArgumentParser(
        description="Configure AnythingLLM workspaces"
    )
    
    parser.add_argument(
        "--config",
        help="Configuration file (JSON)"
    )
    
    parser.add_argument(
        "--create-example",
        action="store_true",
        help="Create example configuration file"
    )
    
    parser.add_argument(
        "--url",
        default="http://localhost:3001",
        help="AnythingLLM server URL"
    )
    
    parser.add_argument(
        "--api-key",
        help="API key for authentication"
    )
    
    args = parser.parse_args()
    
    if args.create_example:
        create_example_config()
        return
    
    if not args.config:
        print("Error: --config required (or use --create-example)")
        sys.exit(1)
    
    config_file = Path(args.config)
    if not config_file.exists():
        print(f"Error: Config file not found: {config_file}")
        sys.exit(1)
    
    configurator = WorkspaceConfigurator(args.url, args.api_key)
    configurator.configure_from_file(config_file)


if __name__ == "__main__":
    main()
