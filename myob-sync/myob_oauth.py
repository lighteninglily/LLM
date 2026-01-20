#!/usr/bin/env python3
"""
MYOB OAuth2 Authentication Flow
Run this first to get access tokens
"""

import os
import webbrowser
import urllib.parse
from flask import Flask, request
from dotenv import load_dotenv, set_key
import requests

load_dotenv()

app = Flask(__name__)

MYOB_API_KEY = os.getenv("MYOB_API_KEY")
MYOB_API_SECRET = os.getenv("MYOB_API_SECRET")
MYOB_REDIRECT_URI = os.getenv("MYOB_REDIRECT_URI", "http://localhost:8080/callback")

# MYOB OAuth endpoints
AUTH_URL = "https://secure.myob.com/oauth2/account/authorize"
TOKEN_URL = "https://secure.myob.com/oauth2/v1/authorize"

# Scopes - adjust based on what data you need
SCOPES = "CompanyFile"  # For keys created before March 2025
# SCOPES = "sme-general-ledger sme-sales sme-contacts-customer sme-purchases"  # For new keys

@app.route("/")
def index():
    """Start OAuth flow"""
    params = {
        "client_id": MYOB_API_KEY,
        "redirect_uri": MYOB_REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return f'''
    <h1>MYOB OAuth Setup</h1>
    <p>Click the button below to authorize access to your MYOB account:</p>
    <a href="{auth_url}" style="padding: 10px 20px; background: #00a1e0; color: white; text-decoration: none; border-radius: 5px;">
        Connect to MYOB
    </a>
    '''

@app.route("/callback")
def callback():
    """Handle OAuth callback"""
    code = request.args.get("code")
    error = request.args.get("error")
    
    if error:
        return f"<h1>Error</h1><p>{error}</p>"
    
    if not code:
        return "<h1>Error</h1><p>No authorization code received</p>"
    
    # Exchange code for tokens
    token_data = {
        "client_id": MYOB_API_KEY,
        "client_secret": MYOB_API_SECRET,
        "code": code,
        "redirect_uri": MYOB_REDIRECT_URI,
        "grant_type": "authorization_code",
        "scope": SCOPES
    }
    
    response = requests.post(
        TOKEN_URL,
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        return f"<h1>Token Error</h1><pre>{response.text}</pre>"
    
    tokens = response.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    
    # Save tokens to .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    set_key(env_path, "MYOB_ACCESS_TOKEN", access_token)
    set_key(env_path, "MYOB_REFRESH_TOKEN", refresh_token)
    
    # Get company files
    files_response = requests.get(
        "https://api.myob.com/accountright/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "x-myobapi-key": MYOB_API_KEY,
            "x-myobapi-version": "v2"
        }
    )
    
    company_files = files_response.json() if files_response.status_code == 200 else []
    
    files_html = ""
    for cf in company_files:
        cf_id = cf.get("Id", "")
        cf_name = cf.get("Name", "Unknown")
        cf_uri = cf.get("Uri", "")
        files_html += f'''
        <li>
            <strong>{cf_name}</strong><br>
            ID: <code>{cf_id}</code><br>
            URI: <code>{cf_uri}</code>
        </li>
        '''
    
    return f'''
    <h1>Success!</h1>
    <p>Tokens saved to .env file.</p>
    <h2>Your Company Files:</h2>
    <ul>{files_html if files_html else "<li>No company files found</li>"}</ul>
    <p><strong>Next step:</strong> Copy the Company File ID and URI to your .env file:</p>
    <pre>
MYOB_COMPANY_FILE_ID=&lt;ID from above&gt;
MYOB_COMPANY_FILE_URI=&lt;URI from above&gt;
    </pre>
    <p>Then run: <code>python myob_sync.py</code></p>
    '''

if __name__ == "__main__":
    print("\n" + "="*50)
    print("MYOB OAuth Setup")
    print("="*50)
    print(f"\n1. Open http://localhost:8080 in your browser")
    print(f"2. Click 'Connect to MYOB' and sign in")
    print(f"3. Authorize the application")
    print(f"4. Copy Company File details to .env\n")
    
    webbrowser.open("http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=False)
