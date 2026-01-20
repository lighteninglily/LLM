#!/usr/bin/env python3
"""
MYOB to RAGFlow Sync Script
Fetches data from MYOB API and uploads to RAGFlow dataset
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv, set_key

load_dotenv()

# MYOB Configuration
MYOB_API_KEY = os.getenv("MYOB_API_KEY")
MYOB_API_SECRET = os.getenv("MYOB_API_SECRET")
MYOB_ACCESS_TOKEN = os.getenv("MYOB_ACCESS_TOKEN")
MYOB_REFRESH_TOKEN = os.getenv("MYOB_REFRESH_TOKEN")
MYOB_COMPANY_FILE_URI = os.getenv("MYOB_COMPANY_FILE_URI")

# RAGFlow Configuration
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY")
RAGFLOW_BASE_URL = os.getenv("RAGFLOW_BASE_URL", "http://localhost:3002")
RAGFLOW_DATASET_ID = os.getenv("RAGFLOW_DATASET_ID")

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def refresh_token():
    """Refresh MYOB access token"""
    response = requests.post(
        "https://secure.myob.com/oauth2/v1/authorize",
        data={
            "client_id": MYOB_API_KEY,
            "client_secret": MYOB_API_SECRET,
            "refresh_token": MYOB_REFRESH_TOKEN,
            "grant_type": "refresh_token"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        tokens = response.json()
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        set_key(env_path, "MYOB_ACCESS_TOKEN", tokens["access_token"])
        set_key(env_path, "MYOB_REFRESH_TOKEN", tokens["refresh_token"])
        return tokens["access_token"]
    else:
        print(f"Token refresh failed: {response.text}")
        return None


def myob_request(endpoint, params=None):
    """Make authenticated request to MYOB API"""
    global MYOB_ACCESS_TOKEN
    
    url = f"{MYOB_COMPANY_FILE_URI}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {MYOB_ACCESS_TOKEN}",
        "x-myobapi-key": MYOB_API_KEY,
        "x-myobapi-version": "v2"
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    # Token expired - refresh and retry
    if response.status_code == 401:
        print("Token expired, refreshing...")
        MYOB_ACCESS_TOKEN = refresh_token()
        if MYOB_ACCESS_TOKEN:
            headers["Authorization"] = f"Bearer {MYOB_ACCESS_TOKEN}"
            response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"API Error ({endpoint}): {response.status_code} - {response.text}")
        return None


def fetch_customers():
    """Fetch all customers"""
    print("Fetching customers...")
    data = myob_request("Contact/Customer")
    if data and "Items" in data:
        return data["Items"]
    return []


def fetch_suppliers():
    """Fetch all suppliers"""
    print("Fetching suppliers...")
    data = myob_request("Contact/Supplier")
    if data and "Items" in data:
        return data["Items"]
    return []


def fetch_invoices():
    """Fetch all invoices"""
    print("Fetching invoices...")
    data = myob_request("Sale/Invoice")
    if data and "Items" in data:
        return data["Items"]
    return []


def fetch_bills():
    """Fetch all bills/purchases"""
    print("Fetching bills...")
    data = myob_request("Purchase/Bill")
    if data and "Items" in data:
        return data["Items"]
    return []


def fetch_accounts():
    """Fetch chart of accounts"""
    print("Fetching accounts...")
    data = myob_request("GeneralLedger/Account")
    if data and "Items" in data:
        return data["Items"]
    return []


def fetch_transactions():
    """Fetch general ledger transactions"""
    print("Fetching transactions...")
    data = myob_request("GeneralLedger/JournalTransaction")
    if data and "Items" in data:
        return data["Items"]
    return []


def format_customer(customer):
    """Format customer data as readable text"""
    return f"""
Customer: {customer.get('CompanyName', customer.get('DisplayID', 'Unknown'))}
ID: {customer.get('UID', '')}
Display ID: {customer.get('DisplayID', '')}
Company: {customer.get('CompanyName', '')}
Contact: {customer.get('FirstName', '')} {customer.get('LastName', '')}
Email: {customer.get('Email', '')}
Phone: {customer.get('Phone1', '')}
Balance: ${customer.get('CurrentBalance', 0):.2f}
Credit Limit: ${customer.get('CreditLimit', 0):.2f}
Payment Terms: {customer.get('TermsOfPayment', {}).get('Description', 'N/A')}
---
"""


def format_invoice(invoice):
    """Format invoice data as readable text"""
    lines = invoice.get('Lines', [])
    lines_text = "\n".join([
        f"  - {line.get('Description', 'Item')}: ${line.get('Total', 0):.2f}"
        for line in lines[:5]  # Limit to 5 lines
    ])
    
    return f"""
Invoice: {invoice.get('Number', 'Unknown')}
Date: {invoice.get('Date', '')[:10] if invoice.get('Date') else 'N/A'}
Customer: {invoice.get('Customer', {}).get('Name', 'Unknown')}
Status: {invoice.get('Status', '')}
Subtotal: ${invoice.get('Subtotal', 0):.2f}
Tax: ${invoice.get('TotalTax', 0):.2f}
Total: ${invoice.get('TotalAmount', 0):.2f}
Balance Due: ${invoice.get('BalanceDueAmount', 0):.2f}
Items:
{lines_text}
---
"""


def format_account(account):
    """Format account data as readable text"""
    return f"""
Account: {account.get('Name', 'Unknown')}
Number: {account.get('DisplayID', '')}
Type: {account.get('Type', '')}
Classification: {account.get('Classification', '')}
Current Balance: ${account.get('CurrentBalance', 0):.2f}
---
"""


def save_to_file(data, filename):
    """Save data to file"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w') as f:
        f.write(data)
    print(f"Saved: {filepath}")
    return filepath


def upload_to_ragflow(filepath):
    """Upload file to RAGFlow dataset"""
    if not RAGFLOW_API_KEY or not RAGFLOW_DATASET_ID:
        print("RAGFlow API key or Dataset ID not configured. Skipping upload.")
        return False
    
    url = f"{RAGFLOW_BASE_URL}/api/v1/datasets/{RAGFLOW_DATASET_ID}/documents"
    headers = {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}"
    }
    
    with open(filepath, 'rb') as f:
        files = {'file': (os.path.basename(filepath), f, 'text/plain')}
        response = requests.post(url, headers=headers, files=files)
    
    if response.status_code in [200, 201]:
        print(f"Uploaded to RAGFlow: {os.path.basename(filepath)}")
        return True
    else:
        print(f"RAGFlow upload failed: {response.status_code} - {response.text}")
        return False


def main():
    """Main sync function"""
    print("\n" + "="*50)
    print("MYOB to RAGFlow Sync")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")
    
    # Check configuration
    if not MYOB_ACCESS_TOKEN:
        print("Error: MYOB_ACCESS_TOKEN not set. Run myob_oauth.py first.")
        return
    
    if not MYOB_COMPANY_FILE_URI:
        print("Error: MYOB_COMPANY_FILE_URI not set. Complete OAuth setup first.")
        return
    
    # Fetch and format data
    all_data = []
    
    # Customers
    customers = fetch_customers()
    if customers:
        customer_text = f"# MYOB Customers\nExported: {datetime.now().isoformat()}\nTotal: {len(customers)} customers\n\n"
        customer_text += "".join([format_customer(c) for c in customers])
        filepath = save_to_file(customer_text, "myob_customers.txt")
        all_data.append(filepath)
    
    # Invoices
    invoices = fetch_invoices()
    if invoices:
        invoice_text = f"# MYOB Invoices\nExported: {datetime.now().isoformat()}\nTotal: {len(invoices)} invoices\n\n"
        invoice_text += "".join([format_invoice(i) for i in invoices])
        filepath = save_to_file(invoice_text, "myob_invoices.txt")
        all_data.append(filepath)
    
    # Accounts
    accounts = fetch_accounts()
    if accounts:
        account_text = f"# MYOB Chart of Accounts\nExported: {datetime.now().isoformat()}\nTotal: {len(accounts)} accounts\n\n"
        account_text += "".join([format_account(a) for a in accounts])
        filepath = save_to_file(account_text, "myob_accounts.txt")
        all_data.append(filepath)
    
    # Upload to RAGFlow
    print("\n" + "-"*50)
    print("Uploading to RAGFlow...")
    for filepath in all_data:
        upload_to_ragflow(filepath)
    
    print("\n" + "="*50)
    print("Sync Complete!")
    print(f"Files saved to: {OUTPUT_DIR}")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
