# VSMS RAG & Knowledge Graph Pipeline
## Complete System Documentation

**Version:** 2.0  
**Last Updated:** January 28, 2026  
**Author:** Ryan / Cascade AI Assistant

---

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Hardware Infrastructure](#3-hardware-infrastructure)
4. [Software Stack](#4-software-stack)
5. [LLM Models & Usage](#5-llm-models--usage)
6. [Pipeline Scripts](#6-pipeline-scripts)
7. [Data Flow & Process](#7-data-flow--process)
8. [Configuration](#8-configuration)
9. [Directory Structure](#9-directory-structure)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. System Overview

This system transforms **tabular business data** (spreadsheets, CSVs) into a **Knowledge Graph** that can be queried using natural language through RAG (Retrieval-Augmented Generation).

### What It Does
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Spreadsheet    │ ──▶ │   Narrative     │ ──▶ │    Chunked &    │ ──▶ │  Knowledge      │
│  Data (CSV/XLS) │     │   Text (.txt)   │     │    Embedded     │     │  Graph (KG)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
     INPUT                 TRANSFORM              RAGFlow PARSE           KG GENERATION
```

### Key Benefits
- **Natural Language Queries**: Ask questions like "What did South32 order last month?"
- **Entity Relationships**: Automatically extracts companies, products, locations, and their connections
- **Scalable**: Handles thousands of records across multiple files
- **Local & Private**: All processing happens on local hardware - no cloud APIs

---

## 2. Architecture Diagram

### High-Level Architecture
```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                              LOCAL WORKSTATION                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           NVIDIA RTX 5080 (16GB VRAM)                           │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                    vLLM Server (Port 8000)                               │   │ │
│  │  │                    Qwen2.5-7B-Instruct-AWQ                               │   │ │
│  │  │                    (4-bit quantized, ~6GB VRAM)                          │   │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                              Docker Services                                     │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │ │
│  │  │   RAGFlow    │  │ Elasticsearch│  │    MySQL     │  │    MinIO     │        │ │
│  │  │  Port 3002   │  │  Port 1200   │  │  Port 5455   │  │  Port 9000   │        │ │
│  │  │  (Web UI)    │  │  (Search)    │  │  (Metadata)  │  │  (Storage)   │        │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘        │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                          │ │
│  │  │  Xinference  │  │    Redis     │  │ AnythingLLM  │                          │ │
│  │  │  Port 9997   │  │  Port 6379   │  │  Port 3001   │                          │ │
│  │  │  (Reranker)  │  │  (Cache)     │  │  (Alt UI)    │                          │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                          │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                         Python Pipeline Scripts                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │ │
│  │  │  analyze.py  │  │ transform.py │  │ entity_      │  │ setup_       │        │ │
│  │  │              │  │              │  │ normalizer.py│  │ ragflow.py   │        │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘        │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram
```
                                    TRANSFORMATION PIPELINE
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│  ┌─────────┐    ┌──────────┐    ┌──────────────┐    ┌─────────┐    ┌───────────────┐  │
│  │  CSV/   │    │ Entity   │    │   LLM        │    │ Chunked │    │   RAGFlow     │  │
│  │  XLS    │───▶│ Normalizer│───▶│   Transform  │───▶│  .txt   │───▶│   Upload      │  │
│  │  Files  │    │          │    │   (Qwen2.5)  │    │  Files  │    │   & Parse     │  │
│  └─────────┘    └──────────┘    └──────────────┘    └─────────┘    └───────────────┘  │
│       │              │                 │                 │                │            │
│       ▼              ▼                 ▼                 ▼                ▼            │
│  Read records   Standardize      Convert to        Split into       Embed with        │
│  from files     entity names     narrative text    paragraphs      nomic-embed-text   │
│                 (companies,      with source                                          │
│                  mines, etc)     context                                              │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘

                                   KNOWLEDGE GRAPH GENERATION
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │  Embedded   │    │   Entity    │    │ Relationship│    │   Queryable             │ │
│  │  Chunks     │───▶│  Extraction │───▶│  Linking    │───▶│   Knowledge Graph       │ │
│  │             │    │  (Qwen2.5)  │    │             │    │                         │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────────────────┘ │
│        │                  │                  │                       │                 │
│        ▼                  ▼                  ▼                       ▼                 │
│   Parse chunks       Extract:           Create edges:          Query via:             │
│   from documents     - Organizations    - sells_to             - Natural language     │
│                      - Products         - ordered              - Graph traversal      │
│                      - Locations        - delivered_to         - RAG chat             │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Hardware Infrastructure

### Current Configuration

| Component | Specification | Purpose |
|-----------|--------------|---------|
| **CPU** | AMD/Intel (multi-core) | Pipeline orchestration, data processing |
| **RAM** | 32GB+ | Docker services, data loading |
| **GPU** | NVIDIA RTX 5080 (16GB VRAM) | LLM inference (vLLM), embeddings |
| **Storage** | 1.8TB SSD | Data files, Docker volumes, model weights |

### GPU Memory Allocation
```
┌─────────────────────────────────────────────────────────────┐
│                  RTX 5080 VRAM (16GB)                       │
├─────────────────────────────────────────────────────────────┤
│ ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ vLLM Qwen2.5-7B-AWQ (~6GB)                                  │
│ ░░░░░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│                 KV Cache (~4GB dynamic)                      │
│ ░░░░░░░░░░░░░░░░░░░░░░░░████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│                         Embedding ops (~2GB)                 │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████████████████████████░░ │
│                              Free (~4GB headroom)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Software Stack

### Docker Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **RAGFlow** | `infiniflow/ragflow:v0.23.1` | 3002 (UI), 9380 (API) | Core RAG platform with KG support |
| **Elasticsearch** | `elasticsearch:8.11.3` | 1200 | Full-text search, chunk storage |
| **MySQL** | `mysql:8.0.39` | 5455 | Metadata, user data |
| **MinIO** | `quay.io/minio/minio` | 9000-9001 | Object storage for documents |
| **Redis/Valkey** | `valkey/valkey:8` | 6379 | Caching, session storage |
| **vLLM** | `vllm/vllm-openai:latest` | 8000 | LLM inference server |
| **Xinference** | `xprobe/xinference:latest` | 9997 | Reranker model hosting |
| **AnythingLLM** | `mintplexlabs/anythingllm` | 3001 | Alternative chat UI |

### Python Environment

| Package | Version | Purpose |
|---------|---------|---------|
| `pandas` | 3.0.0 | Data manipulation |
| `openpyxl` | 3.1.5 | Excel file reading |
| `requests` | 2.32.5 | HTTP API calls |
| `tqdm` | 4.67.1 | Progress bars |
| `pyyaml` | - | Config file parsing |

---

## 5. LLM Models & Usage

### Primary LLM: Qwen2.5-7B-Instruct-AWQ

| Property | Value |
|----------|-------|
| **Model** | `Qwen/Qwen2.5-7B-Instruct-AWQ` |
| **Quantization** | AWQ 4-bit |
| **VRAM Usage** | ~6GB |
| **Context Window** | 32,768 tokens |
| **Server** | vLLM (OpenAI-compatible API) |
| **Endpoint** | `http://localhost:8000/v1` |

#### Usage in Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Qwen2.5-7B Usage                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  1. ANALYSIS (analyze.py)                                                       │
│     ┌─────────────────────────────────────────────────────────────────────┐    │
│     │ Input: Sample records from CSV/XLS                                   │    │
│     │ Output: Entity types, relationships, lookup tables                   │    │
│     │ Tokens: ~2,000 per analysis                                          │    │
│     └─────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  2. TRANSFORMATION (transform.py)                                               │
│     ┌─────────────────────────────────────────────────────────────────────┐    │
│     │ Input: Batch of 20 records + prompt template                         │    │
│     │ Output: Narrative paragraphs with entity names                       │    │
│     │ Tokens: ~3,500 per batch (prompt + records + output)                 │    │
│     └─────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  3. KG EXTRACTION (RAGFlow internal)                                            │
│     ┌─────────────────────────────────────────────────────────────────────┐    │
│     │ Input: Embedded chunk                                                │    │
│     │ Output: Entities + relationships (triples)                           │    │
│     │ Tokens: ~500 per chunk                                               │    │
│     └─────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Embedding Model: nomic-embed-text

| Property | Value |
|----------|-------|
| **Model** | `nomic-embed-text` |
| **Provider** | Ollama (via RAGFlow) |
| **Context Limit** | 8,192 tokens |
| **Chunk Size Used** | 128 tokens (safe margin) |
| **Dimensions** | 768 |

### Reranker Model: BGE-Reranker-v2-M3

| Property | Value |
|----------|-------|
| **Model** | `bge-reranker-v2-m3` |
| **Provider** | Xinference |
| **Endpoint** | `http://localhost:9997` |
| **Purpose** | Re-rank retrieved chunks for better relevance |

---

## 6. Pipeline Scripts

### Script Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SCRIPT HIERARCHY                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  run_full_pipeline_v2.sh  ◄── ORCHESTRATOR (runs everything)                    │
│         │                                                                        │
│         ├──▶ transform.py ◄── Converts CSV/XLS to narrative text                │
│         │         │                                                              │
│         │         └──▶ entity_normalizer.py ◄── Standardizes entity names       │
│         │                                                                        │
│         ├──▶ RAGFlow API ◄── Upload, parse, chunk                               │
│         │                                                                        │
│         └──▶ (Manual) RAGFlow UI ◄── Start KG generation                        │
│                                                                                  │
│  analyze.py ◄── (Optional) Analyze files to determine entity types              │
│                                                                                  │
│  setup_ragflow.py ◄── Create datasets, configure RAGFlow                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Script Details

#### 1. `run_full_pipeline_v2.sh` - Main Orchestrator
```bash
# Location: /home/ryan/Documents/VSMS/ragflow_automation/run_full_pipeline_v2.sh
# Purpose: Runs the complete pipeline end-to-end

# What it does:
# 1. Transforms all files in v2_batch1, v2_batch2, v2_batch3
# 2. Clears existing documents from RAGFlow dataset
# 3. Uploads all transformed .txt files
# 4. Triggers chunk parsing
# 5. Waits for completion
# 6. Prints instructions for manual KG start

# Usage:
./run_full_pipeline_v2.sh              # Run in foreground
nohup ./run_full_pipeline_v2.sh &      # Run in background
tail -f pipeline_v2.log                # Monitor progress
```

#### 2. `transform.py` - Data Transformation
```python
# Location: /home/ryan/Documents/VSMS/ragflow_automation/transform.py
# Purpose: Convert tabular data to narrative text optimized for KG extraction

# Key Features:
# - Reads CSV, XLS, XLSM files
# - Normalizes entity names via entity_normalizer.py
# - Calls Qwen2.5 LLM to generate narrative paragraphs
# - Adds source context (file name, schema) to output
# - Splits large files to prevent embedding errors
# - Limits paragraph length to 400 characters

# Usage:
python transform.py --input ./v2_batch1 --output ./output --verbose
```

#### 3. `entity_normalizer.py` - Entity Standardization
```python
# Location: /home/ryan/Documents/VSMS/ragflow_automation/entity_normalizer.py
# Purpose: Ensure consistent entity naming across all records

# Mappings Include:
# - 50+ company name variations → canonical names
# - 40+ mine site names with state codes (NSW/QLD)
# - Product code standardization

# Example:
# "SOUTH 32" → "SOUTH32"
# "Appin" → "APPIN MINE, NSW"
# "anglo american" → "ANGLO AMERICAN"
```

#### 4. `analyze.py` - File Analysis
```python
# Location: /home/ryan/Documents/VSMS/ragflow_automation/analyze.py
# Purpose: Analyze input files to determine entity types and relationships

# Output (config/analysis_output.json):
# - entity_types: [organization, product, location]
# - relationships: [{from: org, to: product, type: sells}, ...]
# - lookup_tables: files that are reference data only
```

#### 5. `setup_ragflow.py` - RAGFlow Configuration
```python
# Location: /home/ryan/Documents/VSMS/ragflow_automation/setup_ragflow.py
# Purpose: Create and configure RAGFlow datasets via API

# Capabilities:
# - Create new datasets (knowledgebases)
# - Configure embedding models
# - Set chunk parameters
# - Manage document uploads
```

---

## 7. Data Flow & Process

### Complete Pipeline Flow

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: DATA PREPARATION                                                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   Raw Excel/CSV Files                     Organized Batches                            │
│   ┌─────────────────┐                    ┌─────────────────┐                           │
│   │ Sales Report.xls│                    │ v2_batch1/      │ (10 files)               │
│   │ Inventory.csv   │    ─────────▶      │ v2_batch2/      │ (10 files)               │
│   │ Orders.xlsm     │    Organize        │ v2_batch3/      │ (21 files)               │
│   │ Production.csv  │                    └─────────────────┘                           │
│   └─────────────────┘                                                                  │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: TRANSFORMATION (transform.py)                                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐               │
│   │ Read Records    │      │ Normalize       │      │ LLM Transform   │               │
│   │                 │ ───▶ │ Entity Names    │ ───▶ │ (Qwen2.5)       │               │
│   │ pandas.read_csv │      │                 │      │                 │               │
│   │ openpyxl        │      │ entity_         │      │ 20 records/batch│               │
│   └─────────────────┘      │ normalizer.py   │      │ ~3500 tokens    │               │
│                            └─────────────────┘      └─────────────────┘               │
│                                                              │                         │
│   INPUT (CSV row):                                           ▼                         │
│   ┌─────────────────────────────────────────────────────────────────┐                 │
│   │ Customer: South32, Product: R500L5.60Blk, Qty: 5000, Mine: Appin│                 │
│   └─────────────────────────────────────────────────────────────────┘                 │
│                                                                                         │
│   OUTPUT (Narrative):                                                                  │
│   ┌─────────────────────────────────────────────────────────────────┐                 │
│   │ [Source: Sales_Report.csv | Type: sales_record]                 │                 │
│   │ SOUTH32 placed order for 5,000 units of R500L5.60Blk - Rebar    │                 │
│   │ 500L 5.6m Black for delivery to APPIN MINE, NSW.                │                 │
│   └─────────────────────────────────────────────────────────────────┘                 │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: UPLOAD TO RAGFLOW (via API)                                                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   Transformed .txt Files              RAGFlow Dataset                                  │
│   ┌─────────────────┐                ┌─────────────────────────────┐                  │
│   │ Sales_Report.txt│                │ ASW Sales Orders V2         │                  │
│   │ Inventory.txt   │  ────────▶     │ (Improved)                  │                  │
│   │ Orders.txt      │  POST /api/v1/ │                             │                  │
│   │ Production.txt  │  documents     │ Dataset ID: 202ece22fb...   │                  │
│   └─────────────────┘                └─────────────────────────────┘                  │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: CHUNK PARSING (RAGFlow)                                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   Documents                          Chunks                    Embeddings              │
│   ┌─────────┐                       ┌─────────┐              ┌─────────────┐           │
│   │ .txt    │   Split by tokens     │ Chunk 1 │   Embed     │ [0.23, 0.45,│           │
│   │ files   │ ───────────────────▶  │ Chunk 2 │ ──────────▶ │  0.12, ...]  │           │
│   │         │   128 tokens max      │ Chunk 3 │  nomic-     │ 768 dims     │           │
│   └─────────┘                       │ ...     │  embed-text └─────────────┘           │
│                                     └─────────┘                                        │
│                                                                                         │
│   Chunk Token Limit: 128 (safe for 8192 embedding context)                             │
│   Paragraph Limit: 400 characters (~100 tokens)                                        │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: KNOWLEDGE GRAPH GENERATION (RAGFlow UI)                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   For Each Chunk:                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐                 │
│   │ 1. Extract entities (organizations, products, locations)        │                 │
│   │ 2. Identify relationships (sells, ordered, delivered_to)        │                 │
│   │ 3. Create graph triples (subject, predicate, object)            │                 │
│   │ 4. Link to existing entities in graph                           │                 │
│   └─────────────────────────────────────────────────────────────────┘                 │
│                                                                                         │
│   Example Triple:                                                                       │
│   ┌─────────────┐      ordered       ┌─────────────┐                                  │
│   │   SOUTH32   │ ─────────────────▶ │ R500L5.60Blk│                                  │
│   │ (Organization)│                   │  (Product)  │                                  │
│   └─────────────┘                    └─────────────┘                                  │
│          │                                                                             │
│          │ delivers_to                                                                 │
│          ▼                                                                             │
│   ┌─────────────┐                                                                      │
│   │ APPIN MINE  │                                                                      │
│   │  (Location) │                                                                      │
│   └─────────────┘                                                                      │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: QUERY & RETRIEVAL                                                              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   User Query                          Retrieved Context              LLM Response      │
│   ┌─────────────────┐                ┌─────────────────┐          ┌─────────────────┐ │
│   │"What did South32│                │ Relevant chunks │          │"South32 ordered │ │
│   │ order last      │ ──▶ Embed ──▶  │ from KG +       │ ──▶ LLM  │ 5,000 units of  │ │
│   │ month?"         │     & Search   │ vector search   │    ──▶   │ rebar for Appin │ │
│   └─────────────────┘                └─────────────────┘          │ Mine..."        │ │
│                                                                    └─────────────────┘ │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Configuration

### Main Configuration (`config/settings.yaml`)

```yaml
# Hardware profile
hardware_profile: "5080"  # Options: "5080", "5090"

# LLM Settings
llm:
  analysis:
    provider: "vllm"
    model: "Qwen/Qwen2.5-7B-Instruct-AWQ"
    endpoint: "http://localhost:8000/v1"
  
  transform:
    provider: "vllm"
    model: "Qwen/Qwen2.5-7B-Instruct-AWQ"
    endpoint: "http://localhost:8000/v1"
    batch_size: 20        # Records per LLM call
    parallel_calls: 2     # Concurrent requests

# RAGFlow Settings
ragflow:
  endpoint: "http://localhost:9380"
  api_key: "ragflow-xxx..."
  embedding_model: "nomic-embed-text@Ollama"
  chunk_token_num: 128    # Safe for embedding context

# KG Settings
kg:
  max_records_per_file: 500   # Split large files
  max_chunks_per_kb: 5000     # Warning threshold
```

### Transform Prompt (`prompts/transform.txt` - V2)

Key features of the V2 prompt:
1. **Source context header** - Preserves file origin
2. **Canonical entity naming** - Uses aliases for consistency
3. **Explicit relationship phrases** - "ordered", "delivered to", "produced by"
4. **Paragraph length limit** - Max 400 characters
5. **Triple-friendly structure** - Easy for KG extraction

---

## 9. Directory Structure

```
/home/ryan/Documents/VSMS/ragflow_automation/
├── .venv/                      # Python virtual environment
├── config/
│   ├── settings.yaml           # Main configuration
│   └── analysis_output.json    # Entity analysis results
├── prompts/
│   ├── transform.txt           # Current transform prompt (V2)
│   ├── transform_v1_backup.txt # Previous version backup
│   ├── transform_v2.txt        # V2 prompt source
│   └── analyze.txt             # Analysis prompt
├── logs/                       # Transform and pipeline logs
├── v2_batch1/                  # Input batch 1 (10 files)
├── v2_batch2/                  # Input batch 2 (10 files)
├── v2_batch3/                  # Input batch 3 (21 files)
├── v2_output_full/             # Transformed output files
│
├── analyze.py                  # File analysis script
├── transform.py                # Main transformation script
├── entity_normalizer.py        # Entity name standardization
├── setup_ragflow.py            # RAGFlow API utilities
├── run_full_pipeline_v2.sh     # Main orchestrator script
│
├── requirements.txt            # Python dependencies
├── README.md                   # Basic readme
├── PLAN.md                     # Development plan
└── SYSTEM_DOCUMENTATION.md     # This file
```

---

## 10. Troubleshooting

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| **Embedding context exceeded** | Chunks too large | Reduce `chunk_token_num` to 128 |
| **LLM timeout** | Large batch or slow GPU | Reduce `batch_size` to 10-15 |
| **Entity inconsistency** | Name variations | Add mappings to `entity_normalizer.py` |
| **KG extraction poor quality** | Narrative not structured | Use V2 prompt with explicit relationships |
| **GPU OOM** | VRAM exhausted | Restart vLLM, reduce concurrent requests |

### Monitoring Commands

```bash
# Check pipeline progress
tail -f pipeline_v2.log

# Check GPU usage
nvidia-smi

# Check vLLM status
curl http://localhost:8000/v1/models

# Check RAGFlow API
curl http://localhost:9380/api/v1/system/status -H "Authorization: Bearer $API_KEY"

# Count output files
ls ./v2_output_full/*.txt | wc -l

# Check Docker services
docker ps
```

### Restarting Services

```bash
# Restart vLLM
docker restart local-ai-vllm

# Restart RAGFlow
cd /path/to/ragflow && docker compose restart

# Restart entire stack
docker compose down && docker compose up -d
```

---

## Appendix: Entity Mappings

### Company Aliases (Sample)

| Canonical Name | Aliases |
|----------------|---------|
| SOUTH32 | South32, South 32, S32, SOUTH 32 |
| ANGLO AMERICAN | Anglo American, Anglo, ANGLO |
| GLENCORE | Glencore, GLEN, Glencore Coal |
| BHP | BHP, BHP Billiton, BHPB |
| PEABODY | Peabody, Peabody Energy, PBD |

### Mine Site Mappings (Sample)

| Canonical Name | State | Aliases |
|----------------|-------|---------|
| APPIN MINE, NSW | NSW | Appin, APPIN, Appin Mine |
| MORANBAH NORTH, QLD | QLD | Moranbah, Moranbah North, MNM |
| HUNTER VALLEY, NSW | NSW | Hunter Valley, HVO, Hunter |
| BROADMEADOW, QLD | QLD | Broadmeadow, BMM |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 23, 2026 | Initial pipeline with basic transform |
| 1.5 | Jan 27, 2026 | Added entity normalizer, batch processing |
| 2.0 | Jan 28, 2026 | V2 prompt with source context, improved mappings, context window safety |

---

*Document generated by Cascade AI Assistant*
