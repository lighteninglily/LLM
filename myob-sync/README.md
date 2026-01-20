# MYOB to RAGFlow Sync

Syncs data from MYOB AccountRight/Essentials to RAGFlow for AI-powered querying.

## Setup Steps

### Step 1: Register MYOB API Application

1. Go to https://my.myob.com.au
2. Sign in with your MYOB account
3. Navigate to: **Developer** → **Apps** → **Register App**
4. Fill in:
   - **App Name:** RAGFlow Sync
   - **Redirect URI:** `http://localhost:8080/callback`
5. Copy your **API Key** and **API Secret**

### Step 2: Configure Environment

```bash
cd /home/ryan/.local-ai-server/myob-sync
cp .env.example .env
```

Edit `.env` and fill in:
- `MYOB_API_KEY` - Your API Key from Step 1
- `MYOB_API_SECRET` - Your API Secret from Step 1

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run OAuth Flow

```bash
python myob_oauth.py
```

This will:
1. Open a browser window
2. Ask you to sign in to MYOB
3. Authorize the application
4. Display your Company File details
5. Save tokens to `.env`

Copy the **Company File ID** and **URI** to your `.env` file.

### Step 5: Get RAGFlow API Key

1. Go to http://localhost:3002
2. Click your profile → **API Key**
3. Create a new key and copy it
4. Add to `.env` as `RAGFLOW_API_KEY`

### Step 6: Get RAGFlow Dataset ID

1. In RAGFlow, go to **Dataset**
2. Click on your dataset (e.g., "Company Docs")
3. Copy the ID from the URL: `/dataset/{DATASET_ID}`
4. Add to `.env` as `RAGFLOW_DATASET_ID`

### Step 7: Run Sync

```bash
python myob_sync.py
```

This will:
1. Fetch customers, invoices, accounts from MYOB
2. Format data as readable text files
3. Upload to your RAGFlow dataset

### Step 8: Parse Documents in RAGFlow

1. Go to RAGFlow → Dataset
2. Click on the uploaded documents
3. Click **Parse** to process them

## Scheduling (Optional)

To run sync daily, add to crontab:

```bash
crontab -e
# Add this line (runs at 6 AM daily):
0 6 * * * cd /home/ryan/.local-ai-server/myob-sync && /usr/bin/python3 myob_sync.py >> sync.log 2>&1
```

## Data Synced

- **Customers** - Names, contact details, balances
- **Invoices** - Numbers, dates, amounts, line items
- **Accounts** - Chart of accounts with balances
- **Suppliers** - (can be enabled in script)
- **Bills** - (can be enabled in script)

## Troubleshooting

### Token Expired
Run `python myob_oauth.py` again to get new tokens.

### API Errors
Check that your MYOB subscription includes API access.
