# How RAG Works - Behind the Scenes

## What Happens When You Upload Data

### Automatic Process (No Manual Work)

When you upload a file to AnythingLLM:

```
Your File (CSV, PDF, etc.)
    ↓
1. TEXT EXTRACTION - Reads content from file
    ↓
2. CHUNKING - Splits into ~500 token pieces
    ↓
3. EMBEDDING - Converts each chunk to vector (numbers)
    ↓
4. STORAGE - Saves vectors in LanceDB database
    ↓
DONE - Now searchable by AI
```

### You Don't Need To:
- ✗ Tokenize manually
- ✗ Create embeddings
- ✗ Index data
- ✗ Configure vector database

### System Does Automatically:
- ✓ Extracts text from files
- ✓ Splits into chunks
- ✓ Creates embeddings
- ✓ Indexes in vector database
- ✓ Makes searchable

---

## How It Works: Step-by-Step

### Example: Uploading sales_data.csv

**Your CSV:**
```csv
Product,Sales,Region
Widget A,50000,North
Widget B,30000,South
Widget C,40000,East
```

**Step 1: Text Extraction**
AnythingLLM reads the CSV and converts to text:
```
Product: Widget A, Sales: 50000, Region: North
Product: Widget B, Sales: 30000, Region: South
Product: Widget C, Sales: 40000, Region: East
```

**Step 2: Chunking**
Splits into digestible pieces (each ~500 tokens):
```
Chunk 1: "Product: Widget A, Sales: 50000, Region: North. 
          Product: Widget B, Sales: 30000, Region: South."
Chunk 2: "Product: Widget C, Sales: 40000, Region: East."
```

**Step 3: Embedding (Automatic)**
Uses embedding model (nomic-embed-text) to convert text to vectors:
```
Chunk 1 → [0.234, -0.123, 0.456, ... 768 dimensions]
Chunk 2 → [0.189, -0.234, 0.567, ... 768 dimensions]
```

**Step 4: Storage**
Saves vectors in LanceDB with metadata:
```
Vector Database:
  {vector: [...], text: "Chunk 1", source: "sales_data.csv", page: 1}
  {vector: [...], text: "Chunk 2", source: "sales_data.csv", page: 2}
```

---

## How Queries Work

### When You Ask: "What are total sales by region?"

**Step 1: Your Question is Embedded**
```
"What are total sales by region?"
    ↓
[0.245, -0.134, 0.478, ... 768 dimensions]
```

**Step 2: Vector Search**
LanceDB finds most similar chunks:
```
Similarity Score:
  Chunk 1: 0.92 (very relevant)
  Chunk 2: 0.87 (relevant)
```

**Step 3: Context Assembly**
System builds prompt for Qwen:
```
Context from documents:
"Product: Widget A, Sales: 50000, Region: North
 Product: Widget B, Sales: 30000, Region: South
 Product: Widget C, Sales: 40000, Region: East"

User Question: "What are total sales by region?"

Answer:
```

**Step 4: LLM Generates Answer**
Qwen reads context and generates:
```
"Based on the sales data:
- North: $50,000
- South: $30,000
- East: $40,000
Total: $120,000"
```

---

## Data Types and How They're Handled

### Spreadsheets (CSV, XLSX)

**Upload**: `sales_report.xlsx`

**Extracted as:**
```
Each row becomes searchable text:
"Quarter: Q1, Revenue: 150000, Expenses: 80000, Profit: 70000"
"Quarter: Q2, Revenue: 180000, Expenses: 90000, Profit: 90000"
```

**Best for:**
- Financial data
- Sales reports
- Inventory lists
- Analytics

**Preparation:**
- Clean column names (no special characters)
- Remove empty rows
- One table per sheet (multiple sheets OK)
- Save as CSV or XLSX

### Documents (PDF, DOCX)

**Upload**: `company_policy.pdf`

**Extracted as:**
```
Full text content:
"Vacation Policy: Employees receive 20 days per year..."
"Expense Policy: Submit receipts within 30 days..."
```

**Best for:**
- Policies and procedures
- Reports and analyses
- Contracts
- Manuals

**Preparation:**
- Ensure text is selectable (not scanned image)
- Use OCR for scanned documents first
- Clean formatting

### Code Files (PY, JS, etc.)

**Upload**: `analytics.py`

**Extracted as:**
```
Code with comments:
"def calculate_revenue(sales, costs):
    # Calculate net revenue
    return sales - costs"
```

**Best for:**
- Code documentation
- Technical specs
- Configuration files

---

## Data Preparation Best Practices

### For Spreadsheets

**Good:**
```csv
Product,Revenue,Date
Widget A,50000,2024-01-15
Widget B,30000,2024-01-16
```

**Bad:**
```csv
Product Name ($),Total $$$,When???
Widget A - (special!),50k,Jan
```

**Tips:**
- Clear column headers
- Consistent date formats
- No merged cells
- Numbers as numbers (not "50k")

### For Text Documents

**Good Structure:**
```
# Section Title
Clear paragraph with specific information.

## Subsection
More specific details with examples.
```

**Bad Structure:**
```
alllowercasenotitlesnostructure...
```

**Tips:**
- Use headings (H1, H2, etc.)
- Break into paragraphs
- Include context in each section
- Avoid abbreviations without explanation

### For Mixed Data

If you have:
- Spreadsheet data
- Supporting documents
- Code/configs

**Upload separately:**
1. Financial CSVs → "Finance" workspace
2. Policy PDFs → "Policies" workspace
3. Code files → "Technical" workspace

**Or combined:**
- All in one workspace if related
- LLM understands context across files

---

## API Integration (Your MYOB Question)

### Option 1: Download → Upload (Simple)

```bash
# Download from API
curl https://api.myob.com/data > data.json

# Upload to RAG
python3 bulk-ingest-documents.py \
  --workspace "MYOB Data" \
  --folder ./downloads
```

**Pros:**
- Simple, works immediately
- No code changes needed

**Cons:**
- Manual or scheduled downloads
- Data can become stale

### Option 2: Direct API Connection (Advanced)

**Create connector script:**

```python
# myob-connector.py
import requests
from bulk_ingest_documents import AnythingLLMBulkIngester

# Fetch from MYOB API
response = requests.get(
    "https://api.myob.com/v2/contacts",
    headers={"Authorization": f"Bearer {MYOB_TOKEN}"}
)
data = response.json()

# Convert to CSV
import pandas as pd
df = pd.DataFrame(data['Items'])
df.to_csv('myob_contacts.csv', index=False)

# Upload to RAG
ingester = AnythingLLMBulkIngester()
ingester.upload_document('myob_contacts.csv')
```

**Pros:**
- Always fresh data
- Automated updates

**Cons:**
- Requires API credentials
- More complex setup

### Option 3: Live API Queries (Most Advanced)

**Give LLM function to call MYOB API directly:**

This requires:
1. Custom API wrapper
2. Function calling setup
3. Security considerations

**I can build this if you want direct API integration.**

---

## Common Questions

### Q: Does it understand my spreadsheet structure?
**A:** Yes! The system preserves column headers and row relationships. When you ask about "sales by region," it understands the Region column.

### Q: Can I upload 1000 files at once?
**A:** Yes! Use `bulk-ingest-documents.py --recursive` to upload entire folders. System processes each file and indexes all content.

### Q: How much data can it handle?
**A:** RTX 5090 (32GB) can index:
- ~50GB of documents
- Millions of chunks
- Instant retrieval

### Q: Will it mix data from different files?
**A:** Only within same workspace. If you ask about "total sales," it searches ALL files in that workspace and combines information.

### Q: Do I need to re-upload if data changes?
**A:** Yes. RAG is snapshot-based:
- Upload once → Data is indexed
- To update → Re-upload new file
- Old version replaced

For constantly changing data, consider API integration.

### Q: Can it do calculations on my data?
**A:** Yes! The LLM can:
- Read numbers from your CSVs
- Perform calculations
- Aggregate data
- Compare values

Example:
```
You: "What's the average revenue across all regions?"
AI: Reads all rows, calculates average, gives answer
```

---

## What You Actually Need to Do

### 1. Prepare Files (5 minutes)
- Clean column names
- Remove empty rows
- Consistent formats

### 2. Upload (Automatic)
```bash
python3 bulk-ingest-documents.py \
  --workspace "My Data" \
  --folder /path/to/files \
  --recursive
```

### 3. Done!
Ask questions immediately:
- "What were Q4 sales?"
- "Show trends by product"
- "Summarize all policies"

**System handles everything else automatically.**

---

## Technical Details (For Understanding)

### Embedding Model
- **Model**: nomic-embed-text (runs on CPU)
- **Dimensions**: 768
- **Speed**: ~1000 chunks/second
- **Quality**: Understands semantic meaning

### Vector Database
- **Engine**: LanceDB
- **Storage**: ~/.local-ai-server/data/anythingllm/lancedb
- **Format**: Apache Arrow
- **Search**: ANN (Approximate Nearest Neighbor)

### Chunking Strategy
- **Size**: ~500 tokens per chunk
- **Overlap**: 50 tokens between chunks
- **Method**: Sentence-aware splitting
- **Preserves**: Context and relationships

### Search Process
- **Algorithm**: Cosine similarity
- **Threshold**: 0.25 (configurable)
- **Top Results**: 4 chunks (configurable)
- **Reranking**: By relevance score

---

## Summary: What System Does For You

**Automatically:**
1. ✓ Extracts text from any supported file
2. ✓ Splits into optimal chunks
3. ✓ Creates embeddings (vectors)
4. ✓ Indexes in vector database
5. ✓ Searches when you ask questions
6. ✓ Combines relevant information
7. ✓ Generates answers with Qwen

**You just:**
1. Upload files
2. Ask questions
3. Get answers from YOUR data

**No tokenization, indexing, or database management needed!**
