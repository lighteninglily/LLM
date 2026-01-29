# RAGFlow Automation Toolkit - Complete Plan

## Overview

**Goal:** Automatically ingest ANY unknown dataset into RAGFlow with optimal KG configuration.

**Hardware:**
- Current: RTX 5080 (16GB) - design for this
- Future: RTX 5090 (32GB) - easy upgrade path

**Approach:** LLM-driven transformation (Option B - most reliable)

---

## Critical Learnings (From KG Debugging)

| Issue | Root Cause | Solution |
|-------|------------|----------|
| KG takes hours, no progress | Files create 6000-8000 chunks each | **Split files to max 500 records** |
| 0 entities in ES for long time | Entities save per-document, not per-chunk | **Time estimation + progress logging** |
| vLLM context overflow | Default 32K too small | **Require 64K context config** |
| KG processing slow | ~1-2 min per chunk | **Warn user, estimate time upfront** |
| Lookup tables waste KG time | Reference files don't need entities | **Exclude lookup tables from KG** |

---

## System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                                YOUR DATA                                        │
│                                                                                 │
│   /input_data/                                                                  │
│   ├── file1.csv                                                                 │
│   ├── file2.txt                                                                 │
│   ├── export.json                                                               │
│   └── ...                                                                       │
└────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: ANALYZE                                                                │
│  ════════════════                                                               │
│  Script: analyze.py                                                             │
│  LLM: Qwen (via Ollama or vLLM)                                                │
│                                                                                 │
│  ┌─────────────────┐         ┌─────────────────┐                               │
│  │ Sample 100 lines│────────▶│ LLM Analysis    │                               │
│  │ from each file  │         │                 │                               │
│  └─────────────────┘         │ "What entities  │                               │
│                              │  exist? What    │                               │
│                              │  relationships? │                               │
│                              │  Need transform?"│                               │
│                              └────────┬────────┘                               │
│                                       │                                         │
│                                       ▼                                         │
│  OUTPUT: config.json                                                            │
│  {                                                                              │
│    "dataset_name": "Auto-detected or user-provided",                            │
│    "entity_types": ["person", "location", "organization", ...],                 │
│    "needs_transformation": true,                                                │
│    "data_format": "relational|narrative|mixed",                                 │
│    "files": [                                                                   │
│      {"name": "file1.csv", "transform": true, "type": "relational"},            │
│      {"name": "file2.txt", "transform": false, "type": "narrative"}             │
│    ],                                                                           │
│    "lookup_tables": [                                                           │
│      {"file": "countries.csv", "key": "id", "value": "name"}                    │
│    ]                                                                            │
│  }                                                                              │
└────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: TRANSFORM (Only if needed)                                            │
│  ═══════════════════════════════════                                           │
│  Script: transform.py                                                          │
│  LLM: Qwen (via Ollama) - batched for speed                                    │
│                                                                                 │
│  For each file marked "transform": true:                                        │
│                                                                                 │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐   │
│  │ Load lookup     │         │ Batch records   │         │ LLM transforms  │   │
│  │ tables into     │────────▶│ (20-50 at a    │────────▶│ to narrative    │   │
│  │ memory          │         │ time)           │         │ text            │   │
│  └─────────────────┘         └─────────────────┘         └────────┬────────┘   │
│                                                                   │            │
│  PROMPT TO LLM:                                                   │            │
│  ┌────────────────────────────────────────────────────────────┐   │            │
│  │ Convert these database records to readable paragraphs.     │   │            │
│  │ Use these lookups: country_id 5 = "Bangladesh", ...        │   │            │
│  │                                                            │   │            │
│  │ Records:                                                   │   │            │
│  │ 1. station_id: 36, name: Dhaka, country_id: 5              │   │            │
│  │ 2. station_id: 37, name: Rajshahi, country_id: 5           │   │            │
│  │                                                            │   │            │
│  │ Output format: One paragraph per record.                   │   │            │
│  └────────────────────────────────────────────────────────────┘   │            │
│                                                                   │            │
│  LLM OUTPUT:                                                      ▼            │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │ Dhaka is a border station located in Bangladesh, established in 2018. │    │
│  │                                                                        │    │
│  │ Rajshahi is a border station located in Bangladesh, established in... │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
│  OUTPUT: /output_data/*.txt (transformed narrative files)                       │
│                                                                                 │
│  FILE SPLITTING (Critical for KG performance):                                  │
│  - Max 500 records per output file                                              │
│  - Large files split: data_001.txt, data_002.txt, ...                          │
│  - Each file → ~500 chunks → ~12 hours KG time max                             │
└────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: SETUP RAGFLOW                                                         │
│  ═════════════════════                                                         │
│  Script: setup_ragflow.py                                                      │
│  Uses: RAGFlow REST API (localhost:9380)                                       │
│                                                                                 │
│  3a. Create Knowledge Base                                                      │
│      POST /api/v1/datasets                                                      │
│      - name: from config.json                                                   │
│      - embedding_model: nomic-embed-text@Ollama                                │
│      - entity_types: from config.json                                          │
│      - chunk_size: 512 (configurable)                                          │
│                                                                                 │
│  3b. Upload Files                                                               │
│      POST /api/v1/datasets/{id}/documents                                       │
│      - Upload all files from /output_data/                                      │
│                                                                                 │
│  3c. Parse Documents                                                            │
│      POST /api/v1/datasets/{id}/chunks                                          │
│      - Wait for completion with progress bar                                    │
│                                                                                 │
│  3d. Generate Knowledge Graph                                                   │
│      POST /api/v1/datasets/{id}/graphrag                                       │
│      - Estimate time: chunks × 1.5 min                                         │
│      - Show progress: "Doc 3/10 complete, ~2hrs remaining"                     │
│      - Monitor until complete                                                   │
│                                                                                 │
│  3e. (Optional) Generate RAPTOR                                                 │
│      POST /api/v1/datasets/{id}/run_raptor                                     │
│                                                                                 │
│  3f. Create Chat Assistant                                                      │
│      POST /api/v1/chats                                                         │
│      - Link to dataset                                                          │
│      - Enable use_kg: true                                                      │
│      - Set system prompt with {knowledge} variable                             │
└────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                            ┌─────────────────┐
                            │   ✓ COMPLETE    │
                            │                 │
                            │ Chat assistant  │
                            │ ready to use    │
                            └─────────────────┘
```

---

## File Structure

```
ragflow_automation/
├── analyze.py              # Step 1: LLM analyzes data structure
├── transform.py            # Step 2: LLM transforms data to narrative (with file splitting)
├── setup_ragflow.py        # Step 3: API automation (with time estimation)
├── main.py                 # Master script - runs all steps + preflight checks
├── config/
│   ├── settings.yaml       # User configuration (LLM endpoints, KG settings)
│   └── analysis_output.json # Output from Step 1
├── prompts/
│   ├── analyze_prompt.txt  # Prompt template for data analysis
│   └── transform_prompt.txt # Prompt template for transformation
├── logs/                   # Auto-created, stores all LLM calls
└── README.md               # Usage instructions + vLLM config requirements
```

---

## Configuration File (settings.yaml)

```yaml
# Hardware profile (switch when 5090 arrives)
hardware_profile: "5080"  # Options: "5080", "5090"

# LLM Settings
llm:
  # For analysis (quality matters most)
  analysis:
    provider: "vllm"  # or "ollama"
    model: "Qwen/Qwen2.5-7B-Instruct-AWQ"
    endpoint: "http://localhost:8000/v1"
  
  # For transformation (speed matters)
  transform:
    provider: "vllm"
    model: "Qwen/Qwen2.5-7B-Instruct-AWQ"
    endpoint: "http://localhost:8000/v1"
    batch_size: 20  # Records per LLM call
    parallel_calls: 2  # Concurrent LLM requests

# RAGFlow Settings
ragflow:
  endpoint: "http://localhost:9380"
  api_key: "ragflow-xxxxx"  # Get from RAGFlow UI
  embedding_model: "nomic-embed-text@Ollama"
  chunk_token_num: 512
  
# KG Optimization Settings (Critical!)
kg:
  max_records_per_file: 500    # Split files exceeding this (prevents huge chunk counts)
  max_chunks_per_kb: 5000      # Warn if KB exceeds this
  time_per_chunk_minutes: 1.5  # For time estimation
  warn_time_hours: 4           # Warn if estimated time exceeds this

# Processing Settings  
processing:
  skip_transform_if_narrative: true  # Skip transform for already-readable text
  exclude_lookup_from_kg: true       # Lookup tables don't need KG processing
```

---

## Hardware Profiles

### Profile: 5080 (Current)

```yaml
hardware_profile: "5080"
llm:
  analysis:
    model: "qwen2.5:7b-instruct"
  transform:
    model: "qwen2.5:7b-instruct"
    batch_size: 20
    parallel_calls: 2
```

**Performance:** ~10K records/hour

### Profile: 5090 (Future)

```yaml
hardware_profile: "5090"
llm:
  analysis:
    model: "qwen2.5:32b-instruct"  # Better quality
  transform:
    model: "qwen2.5:7b-instruct"   # Keep 7B for speed
    batch_size: 50                  # Larger batches
    parallel_calls: 4               # More parallelism
```

**Performance:** ~30K records/hour (3x faster)

---

## Usage

### Quick Start (One Command)

```bash
cd ragflow_automation

# Process a dataset end-to-end
python main.py --input /path/to/data --name "My Dataset"
```

### Step-by-Step (For Testing/Debugging)

```bash
# Step 1: Analyze data structure
python analyze.py --input /path/to/data --output config/analysis_output.json

# Review the analysis
cat config/analysis_output.json

# Step 2: Transform data (if needed)
python transform.py --config config/analysis_output.json --output /path/to/output

# Step 3: Setup RAGFlow
python setup_ragflow.py --config config/analysis_output.json --data /path/to/output
```

### Test with Small Dataset

```bash
# Create test data folder with 2-3 small files
mkdir test_data
cp sample1.csv sample2.txt test_data/

# Run with verbose output
python main.py --input test_data --name "Test KB" --verbose
```

---

## How Each Script Works

### 1. analyze.py

```
INPUT:  Folder with data files
OUTPUT: config/analysis_output.json

PROCESS:
1. List all files in input folder
2. For each file:
   - Read first 100 lines as sample
   - Detect format (CSV, JSON, TXT, etc.)
3. Send all samples to LLM with analysis prompt
4. LLM returns:
   - entity_types to extract
   - whether transformation needed
   - lookup table relationships
5. Save to JSON config
```

### 2. transform.py

```
INPUT:  config/analysis_output.json + original data files
OUTPUT: Transformed .txt files

PROCESS:
1. Load config
2. Build lookup tables from reference files
3. For each file marked for transformation:
   a. Read records in batches
   b. Send batch + lookups to LLM
   c. LLM returns narrative paragraphs
   d. Write to output file
4. Copy non-transform files as-is
```

### 3. setup_ragflow.py

```
INPUT:  config/analysis_output.json + transformed data files
OUTPUT: RAGFlow KB with KG ready

PROCESS:
1. Load config
2. Create KB via API with entity_types
3. Upload all files
4. Trigger parsing, wait for completion
5. Trigger KG generation, wait for completion
6. Create chat assistant with KG enabled
7. Print success message with KB ID
```

---

## Preflight Checks (main.py)

Before any processing begins, main.py runs these checks:

```
┌─────────────────────────────────────────────────────────────────┐
│  PREFLIGHT CHECKS                                               │
├─────────────────────────────────────────────────────────────────┤
│  ✓ vLLM reachable at endpoint                                   │
│  ✓ vLLM context length >= 64K (required for KG)                │
│  ✓ RAGFlow API reachable                                        │
│  ✓ RAGFlow API key valid                                        │
│  ✓ Ollama embedding model available                             │
│  ✓ Input folder exists and has files                            │
│  ✓ Estimated chunks < 5000 (or user confirms)                   │
│  ✓ Estimated KG time shown to user                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Error Handling

| Error | Cause | Auto-Recovery |
|-------|-------|---------------|
| LLM timeout | Model overloaded | Retry 3x with backoff |
| Context too long | Batch too large | Reduce batch size by 50%, retry |
| RAGFlow API error | Service issue | Retry with exponential backoff |
| File too large | >500 records | Auto-split into parts |
| Transform failed | Bad data | Log error, continue with next record |
| KG stalled | Large doc processing | Show "still working" message, continue waiting |
| vLLM context error | Need 64K | Fail fast with config instructions |

---

## Logging

All operations logged to `logs/` folder:
- `analyze_YYYYMMDD_HHMMSS.log`
- `transform_YYYYMMDD_HHMMSS.log`
- `setup_YYYYMMDD_HHMMSS.log`

Includes:
- Every LLM prompt and response
- API calls and responses
- Timing information
- Errors with context

---

## Testing Strategy

### Test 1: Simple CSV
```
test_simple/
└── countries.csv   (10 rows, 3 columns)
```
Expected: No transform needed, direct upload

### Test 2: Relational Data
```
test_relational/
├── stations.csv    (country_id references countries)
└── countries.csv   (lookup table)
```
Expected: Transform resolves country_id → country name

### Test 3: Mixed Format
```
test_mixed/
├── data.csv        (needs transform)
├── readme.txt      (narrative, no transform)
└── reference.json  (lookup data)
```
Expected: Only CSV transformed, TXT copied as-is

---

## vLLM Configuration Requirements

**CRITICAL:** vLLM must be configured for 64K context for KG to work reliably.

In your `docker-compose.yml` or vLLM startup:

```yaml
environment:
  - VLLM_ALLOW_LONG_MAX_MODEL_LEN=1
  - MAX_MODEL_LEN=65536
```

The toolkit's preflight check will verify this before starting.

---

## Upgrade Path: 5080 → 5090

When 5090 arrives:

1. Edit `config/settings.yaml`:
   ```yaml
   hardware_profile: "5090"
   ```

2. Update batch sizes (auto-configured):
   - batch_size: 20 → 50
   - parallel_calls: 2 → 4

3. Run as normal - toolkit auto-adjusts

**No code changes required.**

