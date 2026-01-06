# Data Preparation Guide for RAG

## Quick Reference: What Works Best

### Spreadsheets (CSV, XLSX)

**✓ Good Example:**
```csv
Date,Customer,Product,Quantity,Revenue,Region
2024-01-15,Acme Corp,Widget A,100,50000,North
2024-01-16,Beta Inc,Widget B,75,30000,South
2024-01-17,Gamma LLC,Widget A,120,60000,East
```

**✗ Bad Example:**
```csv
When,Who,What,#,$$,Where??
Jan 15,Acme,Wid-A,100,"50k",N
1/16/24,Beta,B,75,30K,S
```

**Why Good Works:**
- Clear column headers
- Consistent date format
- No abbreviations
- Numbers as numbers
- Full region names

---

## File Type Preparation

### CSV Files

**Checklist:**
- [ ] Column headers are clear and descriptive
- [ ] No special characters in headers (only letters, numbers, underscore)
- [ ] Dates in consistent format (YYYY-MM-DD or MM/DD/YYYY)
- [ ] Numbers without currency symbols or "k" abbreviations
- [ ] No empty columns or rows
- [ ] One table per file (no multiple tables side-by-side)

**Example Cleanup:**

Before:
```csv
Prod Name ($),Total $$$,Date(approx)
Widget-A (special!),50k,Jan
Widget-B,30K,Feb-ish
```

After:
```csv
Product_Name,Revenue,Date
Widget A,50000,2024-01-15
Widget B,30000,2024-02-01
```

### Excel Files (XLSX)

**Checklist:**
- [ ] Each sheet has clear purpose
- [ ] First row is headers
- [ ] No merged cells
- [ ] No hidden columns with important data
- [ ] Remove pivot tables (export as values)
- [ ] Remove charts (data only)
- [ ] Date cells formatted as dates, not text

**Tip:** If complex Excel file, export each sheet as separate CSV for clarity.

### PDF Documents

**Checklist:**
- [ ] Text is selectable (not scanned image)
- [ ] If scanned, run OCR first
- [ ] Remove password protection
- [ ] Include page numbers (helps with citations)
- [ ] Break very large PDFs (>500 pages) into sections

**OCR Tools (if needed):**
```bash
# Linux: Tesseract
tesseract input.pdf output.pdf pdf

# Online: Adobe Acrobat, smallpdf.com
```

### Word Documents (DOCX)

**Checklist:**
- [ ] Use proper headings (Heading 1, 2, 3)
- [ ] Remove track changes/comments
- [ ] Clear formatting
- [ ] Tables converted to simple format
- [ ] No embedded objects that aren't text

---

## Data Organization Strategies

### Strategy 1: By Type

```
Upload Structure:
├── Financial Data/
│   ├── Q1_2024_sales.csv
│   ├── Q2_2024_sales.csv
│   └── annual_budget.xlsx
├── Policies/
│   ├── employee_handbook.pdf
│   ├── expense_policy.docx
│   └── vacation_policy.pdf
└── Technical/
    ├── api_documentation.md
    └── database_schema.txt
```

**Workspaces:**
- "Financial Analysis" → Financial Data folder
- "HR Policies" → Policies folder
- "Technical Docs" → Technical folder

### Strategy 2: By Project

```
Upload Structure:
├── Project_Phoenix/
│   ├── project_plan.docx
│   ├── budget.xlsx
│   ├── status_reports.pdf
│   └── meeting_notes.md
└── Project_Atlas/
    ├── requirements.docx
    ├── costs.xlsx
    └── timeline.pdf
```

**Workspaces:**
- "Phoenix" → All Phoenix files
- "Atlas" → All Atlas files

### Strategy 3: By Time Period

```
Upload Structure:
├── 2024_Q1/
│   ├── sales.csv
│   ├── expenses.csv
│   └── summary.pdf
├── 2024_Q2/
│   ├── sales.csv
│   ├── expenses.csv
│   └── summary.pdf
```

**Workspaces:**
- "Q1 2024" → Q1 files
- "Q2 2024" → Q2 files
- Or single "2024 Data" workspace with all

---

## Common Data Scenarios

### Scenario 1: Financial Spreadsheets

**You Have:** Monthly P&L statements in Excel

**Prepare:**
```bash
1. Open each Excel file
2. Remove formatting/colors (data only)
3. Ensure column headers: Date, Category, Amount, Notes
4. Export as CSV
5. Upload all to "Financial" workspace
```

**Query Examples:**
- "What were total expenses in Q2?"
- "Show revenue trend by month"
- "Compare this year to last year"

### Scenario 2: Policy Documents

**You Have:** PDFs with company policies

**Prepare:**
```bash
1. Check PDFs are searchable (select text)
2. If scanned, run OCR
3. Name files clearly: vacation_policy.pdf, not doc1.pdf
4. Upload to "Policies" workspace
```

**Query Examples:**
- "What is the vacation policy?"
- "How do I submit expenses?"
- "What's the remote work policy?"

### Scenario 3: Customer Data

**You Have:** CRM export CSV

**Prepare:**
```csv
Customer_Name,Contact_Email,Total_Spent,Last_Purchase,Status
Acme Corp,contact@acme.com,150000,2024-01-15,Active
Beta Inc,sales@beta.com,80000,2023-12-20,Active
```

**Query Examples:**
- "Who are my top 10 customers?"
- "Show active customers who haven't purchased in 3 months"
- "Total revenue from active customers"

### Scenario 4: Mixed Format Data

**You Have:**
- Sales CSV files
- PDF invoices
- Email summaries (text files)

**Prepare:**
```bash
# Create organized structure
sales_data/
  ├── csvs/
  │   ├── 2024_sales.csv
  │   └── 2023_sales.csv
  ├── invoices/
  │   ├── invoice_001.pdf
  │   └── invoice_002.pdf
  └── summaries/
      ├── jan_summary.txt
      └── feb_summary.txt

# Upload entire folder
python3 bulk-ingest-documents.py \
  --workspace "Sales Data" \
  --folder ./sales_data \
  --recursive
```

**System Understands:**
- Numbers from CSVs
- Invoice details from PDFs
- Context from summaries
- Relationships between all

---

## Data Cleaning Tips

### Remove Unnecessary Columns

**Before (12 columns):**
```csv
ID,Date,Customer,Product,Qty,Price,Total,Tax,Shipping,Notes,Internal_ID,Last_Modified
```

**After (6 columns):**
```csv
Date,Customer,Product,Quantity,Total,Notes
```

Keep only what you'll query.

### Standardize Values

**Inconsistent:**
```csv
Status
Active
active
ACTIVE
A
```

**Standardized:**
```csv
Status
Active
Active
Active
Active
```

### Handle Missing Data

**Option 1: Remove rows with critical missing data**
```python
df = df.dropna(subset=['Customer', 'Revenue'])
```

**Option 2: Fill with defaults**
```python
df['Notes'] = df['Notes'].fillna('No notes')
```

**Option 3: Leave as-is** (LLM understands "missing" or "N/A")

---

## API Data Preparation

### MYOB API → RAG

**Step 1: Fetch data**
```python
python3 api-connector-myob.py \
  --workspace "MYOB Data" \
  --endpoint invoices \
  --days 90
```

**Step 2: Data is auto-formatted to CSV**
```csv
Invoice_Number,Date,Customer,Amount,Status
INV-001,2024-01-15,Acme Corp,50000,Paid
INV-002,2024-01-16,Beta Inc,30000,Pending
```

**Step 3: Uploaded and indexed automatically**

**Query:**
- "Show unpaid invoices"
- "Total revenue this month"
- "Which customers haven't paid?"

### Other APIs (Same Pattern)

```python
# Fetch from any API
response = requests.get("https://api.example.com/data")
data = response.json()

# Convert to DataFrame
import pandas as pd
df = pd.DataFrame(data)

# Save and upload
df.to_csv('api_data.csv')
python3 bulk-ingest-documents.py --workspace "API Data" --folder .
```

---

## File Naming Best Practices

### Good Names:
```
2024_Q1_sales_by_region.csv
employee_handbook_v2.pdf
myob_invoices_2024-01-15.csv
```

### Bad Names:
```
data.csv
doc1.pdf
download (1).xlsx
```

**Rules:**
- Descriptive
- Include date if time-sensitive
- No spaces (use underscore)
- Lowercase
- Version number if applicable

---

## Size Recommendations

### Per File:
- **CSV**: Up to 100MB (millions of rows OK)
- **PDF**: Up to 50MB per file
- **Excel**: Up to 50MB
- **Text**: Any size

### Per Upload Batch:
- **Recommended**: 100-500 files at once
- **Maximum**: No hard limit, but batch for monitoring

### Total Dataset:
- **RTX 5090 (32GB)**: ~50GB total documents
- **Typical usage**: 10-20GB is comfortable

---

## Validation Checklist

Before uploading, verify:

**Spreadsheets:**
- [ ] Opens in Excel/Google Sheets without errors
- [ ] Column headers make sense
- [ ] No #REF or #VALUE errors
- [ ] Dates display correctly

**Documents:**
- [ ] PDF text is selectable
- [ ] Word doc opens cleanly
- [ ] No password protection
- [ ] Readable font size

**Overall:**
- [ ] Files named descriptively
- [ ] Organized in logical folders
- [ ] Removed duplicates
- [ ] Removed unnecessary files

---

## Quick Start Template

**For Your First Upload:**

```bash
# 1. Create organized folder
mkdir my_data
cd my_data

# 2. Copy files in (clean as needed)
cp /path/to/spreadsheets/*.csv .
cp /path/to/documents/*.pdf .

# 3. Quick check
ls -lh  # Verify files present

# 4. Upload all
cd ~/llm-installer
python3 bulk-ingest-documents.py \
  --workspace "My First Workspace" \
  --folder ~/my_data \
  --recursive

# 5. Test immediately
# Open http://localhost:3001
# Select workspace
# Ask: "What data do I have?"
```

---

## Summary

**You Don't Need:**
- ✗ Manual tokenization
- ✗ Data science skills
- ✗ Database knowledge
- ✗ Complex preprocessing

**You Just Need:**
- ✓ Clean column headers
- ✓ Consistent formats
- ✓ Organized files
- ✓ Remove obvious junk

**System Handles:**
- Text extraction
- Chunking
- Embedding
- Indexing
- Searching

**Upload → Ask Questions → Get Answers**

That's it!
