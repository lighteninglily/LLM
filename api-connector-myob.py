#!/usr/bin/env python3
"""
MYOB API Connector for RAG System

Automatically fetch data from MYOB API and upload to AnythingLLM for analysis.
Can be run manually or scheduled (cron/Task Scheduler).

Usage:
    python3 api-connector-myob.py --workspace "MYOB Data" --endpoint contacts
    python3 api-connector-myob.py --workspace "Sales" --endpoint invoices --days 30
"""

import os
import sys
import json
import argparse
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

class MYOBConnector:
    """Connect to MYOB API and sync data to RAG"""
    
    def __init__(self, api_key: str, company_file_id: str):
        """
        Initialize MYOB connector
        
        Args:
            api_key: MYOB API key
            company_file_id: MYOB company file ID
        """
        self.api_key = api_key
        self.company_file_id = company_file_id
        self.base_url = "https://api.myob.com/accountright"
        self.headers = {
            "x-myobapi-key": api_key,
            "x-myobapi-cftoken": company_file_id,
            "Accept": "application/json"
        }
    
    def fetch_contacts(self) -> pd.DataFrame:
        """Fetch all contacts from MYOB"""
        print("Fetching contacts from MYOB...")
        
        response = requests.get(
            f"{self.base_url}/{self.company_file_id}/Contact/Customer",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('Items', [])
            print(f"  Found {len(items)} contacts")
            return pd.DataFrame(items)
        else:
            raise Exception(f"Failed to fetch contacts: {response.text}")
    
    def fetch_invoices(self, days: int = 30) -> pd.DataFrame:
        """
        Fetch recent invoices
        
        Args:
            days: Number of days to look back
        """
        print(f"Fetching invoices from last {days} days...")
        
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{self.base_url}/{self.company_file_id}/Sale/Invoice",
            headers=self.headers,
            params={"$filter": f"Date ge datetime'{date_from}'"}
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('Items', [])
            print(f"  Found {len(items)} invoices")
            return pd.DataFrame(items)
        else:
            raise Exception(f"Failed to fetch invoices: {response.text}")
    
    def fetch_accounts(self) -> pd.DataFrame:
        """Fetch chart of accounts"""
        print("Fetching accounts...")
        
        response = requests.get(
            f"{self.base_url}/{self.company_file_id}/GeneralLedger/Account",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('Items', [])
            print(f"  Found {len(items)} accounts")
            return pd.DataFrame(items)
        else:
            raise Exception(f"Failed to fetch accounts: {response.text}")
    
    def save_to_csv(self, df: pd.DataFrame, filename: str) -> Path:
        """
        Save DataFrame to CSV
        
        Args:
            df: DataFrame to save
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        output_dir = Path("myob_data")
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / filename
        df.to_csv(filepath, index=False)
        print(f"  Saved to: {filepath}")
        
        return filepath
    
    def upload_to_rag(self, filepath: Path, workspace: str):
        """
        Upload CSV to AnythingLLM
        
        Args:
            filepath: Path to CSV file
            workspace: Workspace name
        """
        print(f"Uploading to workspace: {workspace}")
        
        # Use bulk ingestion script
        from bulk_ingest_documents import AnythingLLMBulkIngester
        
        ingester = AnythingLLMBulkIngester()
        doc_location = ingester.upload_document(filepath)
        
        workspace_slug = workspace.lower().replace(" ", "-")
        ingester.add_document_to_workspace(workspace_slug, doc_location)
        
        print(f"  ✓ Uploaded successfully")


def main():
    parser = argparse.ArgumentParser(
        description="MYOB API Connector for RAG System"
    )
    
    parser.add_argument(
        "--workspace",
        required=True,
        help="AnythingLLM workspace name"
    )
    
    parser.add_argument(
        "--endpoint",
        required=True,
        choices=["contacts", "invoices", "accounts"],
        help="MYOB data endpoint to fetch"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days to look back for invoices (default: 30)"
    )
    
    parser.add_argument(
        "--api-key",
        help="MYOB API key (or set MYOB_API_KEY env var)"
    )
    
    parser.add_argument(
        "--company-id",
        help="MYOB company file ID (or set MYOB_COMPANY_ID env var)"
    )
    
    args = parser.parse_args()
    
    # Get credentials
    api_key = args.api_key or os.getenv("MYOB_API_KEY")
    company_id = args.company_id or os.getenv("MYOB_COMPANY_ID")
    
    if not api_key or not company_id:
        print("Error: MYOB credentials required")
        print("Set via --api-key and --company-id or environment variables:")
        print("  export MYOB_API_KEY=your_key")
        print("  export MYOB_COMPANY_ID=your_company_id")
        sys.exit(1)
    
    print("="*60)
    print("MYOB API Connector")
    print("="*60)
    print()
    
    try:
        connector = MYOBConnector(api_key, company_id)
        
        # Fetch data
        if args.endpoint == "contacts":
            df = connector.fetch_contacts()
            filename = f"myob_contacts_{datetime.now().strftime('%Y%m%d')}.csv"
        elif args.endpoint == "invoices":
            df = connector.fetch_invoices(args.days)
            filename = f"myob_invoices_{datetime.now().strftime('%Y%m%d')}.csv"
        elif args.endpoint == "accounts":
            df = connector.fetch_accounts()
            filename = f"myob_accounts_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # Save to CSV
        filepath = connector.save_to_csv(df, filename)
        
        # Upload to RAG
        connector.upload_to_rag(filepath, args.workspace)
        
        print()
        print("="*60)
        print("Sync Complete!")
        print("="*60)
        print(f"Workspace: {args.workspace}")
        print(f"Records: {len(df)}")
        print()
        print("You can now query this data in AnythingLLM:")
        print(f"  'What are the recent invoices?'")
        print(f"  'Show me all customers'")
        print(f"  'Summarize account balances'")
        print()
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
