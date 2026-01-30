"""
MYOB API Endpoints
Handles OAuth callback and data sync operations
"""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import logging
from pathlib import Path

from services.myob_service import get_myob_service, configure_myob_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/myob", tags=["MYOB"])

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "production.db"


class MYOBConfig(BaseModel):
    api_key: str
    api_secret: str
    redirect_uri: str = "http://localhost:3003/api/myob/callback"


class CompanyFileSelect(BaseModel):
    business_id: str
    cf_username: str = ""
    cf_password: str = ""


@router.post("/configure")
async def configure_myob(config: MYOBConfig):
    """Configure MYOB API credentials."""
    service = configure_myob_service(
        api_key=config.api_key,
        api_secret=config.api_secret,
        redirect_uri=config.redirect_uri
    )
    return {"status": "configured", "auth_url": service.get_auth_url()}


@router.get("/auth-url")
async def get_auth_url():
    """Get the OAuth authorization URL."""
    service = get_myob_service()
    if not service:
        raise HTTPException(status_code=400, detail="MYOB not configured. Call /configure first.")
    
    return {"auth_url": service.get_auth_url()}


@router.get("/callback")
async def oauth_callback(code: str = Query(...), businessId: str = Query(None)):
    """OAuth callback endpoint - receives authorization code from MYOB."""
    service = get_myob_service()
    if not service:
        raise HTTPException(status_code=400, detail="MYOB not configured")
    
    try:
        await service.exchange_code_for_tokens(code, businessId)
        
        # Return success page
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>MYOB Connected</title>
            <style>
                body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #1a1a2e; color: white; }
                .container { text-align: center; padding: 40px; background: #16213e; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
                h1 { color: #4ade80; }
                p { color: #94a3b8; }
                .btn { display: inline-block; margin-top: 20px; padding: 12px 24px; background: linear-gradient(135deg, #8b5cf6, #6366f1); color: white; text-decoration: none; border-radius: 8px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✓ MYOB Connected Successfully!</h1>
                <p>Your MYOB account has been linked.</p>
                <p>You can now sync data from MYOB.</p>
                <a href="/" class="btn">Return to App</a>
            </div>
        </body>
        </html>
        """)
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def get_status():
    """Check MYOB connection status."""
    service = get_myob_service()
    if not service:
        return {"configured": False, "authenticated": False}
    
    return {
        "configured": True,
        "authenticated": service.is_authenticated(),
        "business_id": service.business_id
    }


@router.get("/company-files")
async def get_company_files():
    """Get list of available company files."""
    service = get_myob_service()
    if not service or not service.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated with MYOB")
    
    files = await service.get_company_files()
    return {"company_files": files}


@router.post("/select-company")
async def select_company_file(data: CompanyFileSelect):
    """Select which company file to use."""
    service = get_myob_service()
    if not service:
        raise HTTPException(status_code=400, detail="MYOB not configured")
    
    service.business_id = data.business_id
    service._save_tokens()
    
    return {"status": "selected", "business_id": data.business_id}


@router.post("/sync/customers")
async def sync_customers(cf_username: str = "", cf_password: str = ""):
    """Sync customers from MYOB to local database."""
    service = get_myob_service()
    if not service or not service.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated with MYOB")
    
    try:
        customers = await service.get_customers(cf_username, cf_password)
        
        # Create table if not exists and insert data
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS myob_customers (
                uid TEXT PRIMARY KEY,
                name TEXT,
                display_id TEXT,
                is_active INTEGER,
                addresses TEXT,
                notes TEXT,
                balance REAL,
                credit_limit REAL,
                payment_terms TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        for c in customers:
            cursor.execute("""
                INSERT OR REPLACE INTO myob_customers 
                (uid, name, display_id, is_active, addresses, notes, balance, credit_limit, payment_terms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c.get('UID'),
                c.get('Name') or c.get('CompanyName'),
                c.get('DisplayID'),
                1 if c.get('IsActive', True) else 0,
                str(c.get('Addresses', [])),
                c.get('Notes', ''),
                c.get('CurrentBalance', 0),
                c.get('CreditLimit', 0),
                str(c.get('SellingDetails', {}).get('Terms', {}))
            ))
        
        conn.commit()
        conn.close()
        
        return {"status": "success", "synced": len(customers)}
    except Exception as e:
        logger.error(f"Customer sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/items")
async def sync_items(cf_username: str = "", cf_password: str = ""):
    """Sync inventory items from MYOB to local database."""
    service = get_myob_service()
    if not service or not service.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated with MYOB")
    
    try:
        items = await service.get_items(cf_username, cf_password)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS myob_items (
                uid TEXT PRIMARY KEY,
                number TEXT,
                name TEXT,
                description TEXT,
                is_active INTEGER,
                is_inventoried INTEGER,
                quantity_on_hand REAL,
                quantity_available REAL,
                average_cost REAL,
                base_selling_price REAL,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        for item in items:
            cursor.execute("""
                INSERT OR REPLACE INTO myob_items 
                (uid, number, name, description, is_active, is_inventoried, 
                 quantity_on_hand, quantity_available, average_cost, base_selling_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get('UID'),
                item.get('Number'),
                item.get('Name'),
                item.get('Description', ''),
                1 if item.get('IsActive', True) else 0,
                1 if item.get('IsInventoried', False) else 0,
                item.get('QuantityOnHand', 0),
                item.get('QuantityAvailable', 0),
                item.get('AverageCost', 0),
                item.get('BaseSellingPrice', 0)
            ))
        
        conn.commit()
        conn.close()
        
        return {"status": "success", "synced": len(items)}
    except Exception as e:
        logger.error(f"Items sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/invoices")
async def sync_invoices(cf_username: str = "", cf_password: str = ""):
    """Sync sales invoices from MYOB to local database."""
    service = get_myob_service()
    if not service or not service.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated with MYOB")
    
    try:
        invoices = await service.get_sales_invoices(cf_username, cf_password)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS myob_invoices (
                uid TEXT PRIMARY KEY,
                number TEXT,
                date TEXT,
                customer_name TEXT,
                customer_uid TEXT,
                subtotal REAL,
                total_tax REAL,
                total_amount REAL,
                balance_due REAL,
                status TEXT,
                lines TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        for inv in invoices:
            customer = inv.get('Customer', {})
            cursor.execute("""
                INSERT OR REPLACE INTO myob_invoices 
                (uid, number, date, customer_name, customer_uid, subtotal, 
                 total_tax, total_amount, balance_due, status, lines)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inv.get('UID'),
                inv.get('Number'),
                inv.get('Date'),
                customer.get('Name'),
                customer.get('UID'),
                inv.get('Subtotal', 0),
                inv.get('TotalTax', 0),
                inv.get('TotalAmount', 0),
                inv.get('BalanceDueAmount', 0),
                inv.get('Status'),
                str(inv.get('Lines', []))
            ))
        
        conn.commit()
        conn.close()
        
        return {"status": "success", "synced": len(invoices)}
    except Exception as e:
        logger.error(f"Invoice sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/all")
async def sync_all(cf_username: str = "", cf_password: str = ""):
    """Sync all data from MYOB."""
    results = {}
    
    try:
        results['customers'] = await sync_customers(cf_username, cf_password)
    except Exception as e:
        results['customers'] = {"status": "error", "error": str(e)}
    
    try:
        results['items'] = await sync_items(cf_username, cf_password)
    except Exception as e:
        results['items'] = {"status": "error", "error": str(e)}
    
    try:
        results['invoices'] = await sync_invoices(cf_username, cf_password)
    except Exception as e:
        results['invoices'] = {"status": "error", "error": str(e)}
    
    return results
