"""
MYOB API Integration Service
Handles OAuth authentication and data retrieval from MYOB Business API
"""

import httpx
import json
import base64
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# MYOB API Configuration
MYOB_AUTH_URL = "https://secure.myob.com/oauth2/account/authorize"
MYOB_TOKEN_URL = "https://secure.myob.com/oauth2/v1/authorize"
MYOB_API_BASE = "https://api.myob.com/accountright"

# Token storage path
TOKEN_FILE = Path(__file__).parent.parent.parent / "data" / "myob_tokens.json"
CONFIG_FILE = Path(__file__).parent.parent.parent / "data" / "myob_config.json"


class MYOBService:
    def __init__(self, api_key: str, api_secret: str, redirect_uri: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.refresh_token = None
        self.token_expires = None
        self.business_id = None  # Company file GUID
        self._load_tokens()
    
    def _load_tokens(self):
        """Load saved tokens from file."""
        if TOKEN_FILE.exists():
            try:
                with open(TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
                    self.business_id = data.get('business_id')
                    expires = data.get('token_expires')
                    if expires:
                        self.token_expires = datetime.fromisoformat(expires)
                    logger.info("Loaded MYOB tokens from file")
            except Exception as e:
                logger.error(f"Failed to load MYOB tokens: {e}")
    
    def _save_tokens(self):
        """Save tokens to file."""
        try:
            TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(TOKEN_FILE, 'w') as f:
                json.dump({
                    'access_token': self.access_token,
                    'refresh_token': self.refresh_token,
                    'business_id': self.business_id,
                    'token_expires': self.token_expires.isoformat() if self.token_expires else None
                }, f)
            logger.info("Saved MYOB tokens to file")
        except Exception as e:
            logger.error(f"Failed to save MYOB tokens: {e}")
    
    def get_auth_url(self, scopes: List[str] = None) -> str:
        """Generate OAuth authorization URL for user to visit."""
        if scopes is None:
            # Default scopes for full access
            scopes = [
                "la.global",  # Global access
                "la.sales",   # Sales data
                "la.purchases",  # Purchase data
                "la.inventory",  # Inventory
                "la.contacts",   # Customers/Suppliers
                "la.banking",    # Bank transactions
                "la.payroll",    # Payroll (if needed)
                "la.reports"     # Reports
            ]
        
        import urllib.parse
        scope_str = " ".join(scopes)
        
        params = {
            "client_id": self.api_key,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": scope_str
        }
        
        return f"{MYOB_AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    async def exchange_code_for_tokens(self, code: str, business_id: str = None) -> Dict[str, Any]:
        """Exchange authorization code for access/refresh tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MYOB_TOKEN_URL,
                data={
                    "client_id": self.api_key,
                    "client_secret": self.api_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                    "scope": "la.global"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise Exception(f"Token exchange failed: {response.text}")
            
            data = response.json()
            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']
            self.token_expires = datetime.now() + timedelta(seconds=int(data.get('expires_in', 1200)))
            
            if business_id:
                self.business_id = business_id
            
            self._save_tokens()
            return data
    
    async def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token."""
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MYOB_TOKEN_URL,
                data={
                    "client_id": self.api_key,
                    "client_secret": self.api_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.text}")
                return False
            
            data = response.json()
            self.access_token = data['access_token']
            self.refresh_token = data.get('refresh_token', self.refresh_token)
            self.token_expires = datetime.now() + timedelta(seconds=int(data.get('expires_in', 1200)))
            self._save_tokens()
            return True
    
    async def _ensure_valid_token(self):
        """Ensure we have a valid access token."""
        if not self.access_token:
            raise Exception("Not authenticated. Please complete OAuth flow first.")
        
        # Refresh if expired or expiring soon (within 2 minutes)
        if self.token_expires and datetime.now() >= (self.token_expires - timedelta(minutes=2)):
            if not await self.refresh_access_token():
                raise Exception("Failed to refresh token. Please re-authenticate.")
    
    def _get_headers(self, cf_username: str = "", cf_password: str = "") -> Dict[str, str]:
        """Get headers for MYOB API calls."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "x-myobapi-key": self.api_key,
            "x-myobapi-version": "v2",
            "Accept": "application/json"
        }
        
        # Company file credentials (if required)
        if cf_username or cf_password:
            cf_token = base64.b64encode(f"{cf_username}:{cf_password}".encode()).decode()
            headers["x-myobapi-cftoken"] = cf_token
        
        return headers
    
    async def get_company_files(self) -> List[Dict]:
        """Get list of company files the user has access to."""
        await self._ensure_valid_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                MYOB_API_BASE,
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get company files: {response.text}")
                return []
            
            return response.json()
    
    async def _api_get(self, endpoint: str, cf_username: str = "", cf_password: str = "") -> Dict:
        """Make GET request to MYOB API."""
        await self._ensure_valid_token()
        
        if not self.business_id:
            raise Exception("No company file selected. Set business_id first.")
        
        url = f"{MYOB_API_BASE}/{self.business_id}/{endpoint}"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                url,
                headers=self._get_headers(cf_username, cf_password)
            )
            
            if response.status_code != 200:
                logger.error(f"API request failed: {response.text}")
                raise Exception(f"API request failed: {response.status_code}")
            
            return response.json()
    
    # ==================== Data Retrieval Methods ====================
    
    async def get_customers(self, cf_username: str = "", cf_password: str = "") -> List[Dict]:
        """Get all customers."""
        data = await self._api_get("Contact/Customer", cf_username, cf_password)
        return data.get('Items', [])
    
    async def get_suppliers(self, cf_username: str = "", cf_password: str = "") -> List[Dict]:
        """Get all suppliers."""
        data = await self._api_get("Contact/Supplier", cf_username, cf_password)
        return data.get('Items', [])
    
    async def get_items(self, cf_username: str = "", cf_password: str = "") -> List[Dict]:
        """Get all inventory items."""
        data = await self._api_get("Inventory/Item", cf_username, cf_password)
        return data.get('Items', [])
    
    async def get_sales_invoices(self, cf_username: str = "", cf_password: str = "") -> List[Dict]:
        """Get all sales invoices."""
        data = await self._api_get("Sale/Invoice/Item", cf_username, cf_password)
        return data.get('Items', [])
    
    async def get_purchase_orders(self, cf_username: str = "", cf_password: str = "") -> List[Dict]:
        """Get all purchase orders."""
        data = await self._api_get("Purchase/Order/Item", cf_username, cf_password)
        return data.get('Items', [])
    
    async def get_accounts(self, cf_username: str = "", cf_password: str = "") -> List[Dict]:
        """Get chart of accounts."""
        data = await self._api_get("GeneralLedger/Account", cf_username, cf_password)
        return data.get('Items', [])
    
    async def get_inventory_adjustments(self, cf_username: str = "", cf_password: str = "") -> List[Dict]:
        """Get inventory adjustments."""
        data = await self._api_get("Inventory/Adjustment", cf_username, cf_password)
        return data.get('Items', [])
    
    def is_authenticated(self) -> bool:
        """Check if we have valid tokens."""
        return bool(self.access_token and self.refresh_token)


# Global instance (will be configured from settings)
_myob_service: Optional[MYOBService] = None


def get_myob_service() -> Optional[MYOBService]:
    """Get the global MYOB service instance."""
    global _myob_service
    if _myob_service is None:
        _myob_service = _load_from_config()
    return _myob_service


def _load_from_config() -> Optional[MYOBService]:
    """Load MYOB service from config file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return MYOBService(
                    api_key=config['api_key'],
                    api_secret=config['api_secret'],
                    redirect_uri=config['redirect_uri']
                )
        except Exception as e:
            logger.error(f"Failed to load MYOB config: {e}")
    return None


def configure_myob_service(api_key: str, api_secret: str, redirect_uri: str):
    """Configure the global MYOB service instance."""
    global _myob_service
    _myob_service = MYOBService(api_key, api_secret, redirect_uri)
    return _myob_service
