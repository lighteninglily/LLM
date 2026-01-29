# Intelligent Data Transformation System Plan

**Status: IMPLEMENTED** ✅

## Problem Statement
Semantic embeddings treat discrete values (dates, codes, IDs) as similar when they must be distinguished. "December 3" and "December 8" score ~99% similar, causing retrieval failures.

## Architecture: Universal One-Size-Fits-All Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        YOU PROVIDE: Raw Data Files                          │
│                    (CSV, Excel, JSON, any structured data)                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     STAGE 1: INTELLIGENT SCHEMA ANALYSIS                    │
│  LLM reads sample records and AUTOMATICALLY determines:                     │
│  • What TYPE of data is this?                                               │
│  • What ENTITIES exist?                                                     │
│  • What RELATIONSHIPS connect them?                                         │
│  • Which fields are RETRIEVAL-SENSITIVE? (dates, codes, IDs)               │
│  • What CANONICAL NAMES should be used?                                     │
│  • What TAG FORMAT is needed?                                               │
│                           ZERO CONFIGURATION NEEDED                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     STAGE 2: ADAPTIVE TRANSFORMATION                        │
│  LLM transforms each record using DYNAMIC instructions:                     │
│  • Generates metadata tags based on Stage 1 analysis                       │
│  • Writes narrative optimized for the specific record type                 │
│  • Normalizes entities to canonical forms                                  │
│  • Structures relationships for Knowledge Graph extraction                 │
│                         PROMPT BUILDS ITSELF PER FILE                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              OUTPUT                                         │
│  [META: date=2025-12-03 | machine=CLIFFORD_MMW | product=IMG4-44-2015]     │
│  CLIFFORD MMW produced 800 units of IMG4-44-2015 on December 3, 2025...    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Research-Backed Solution

### 1. METADATA EXTRACTION (Per-File Analysis Enhancement)

The LLM analyzes each file and auto-detects:

```json
{
  "record_type": "production_record",
  "entities": ["machine", "product", "order"],
  "relationships": ["produces", "fulfills"],
  
  "retrieval_sensitive_fields": [
    {
      "field_name": "production_date",
      "field_type": "date",
      "requires_exact_match": true,
      "reason": "Dates are discrete values that embeddings blur",
      "extraction_pattern": "ISO date format YYYY-MM-DD"
    },
    {
      "field_name": "product_code", 
      "field_type": "identifier",
      "requires_exact_match": true,
      "reason": "Codes differ by 1-2 characters, must be distinguished",
      "extraction_pattern": "Alphanumeric code"
    },
    {
      "field_name": "order_number",
      "field_type": "identifier", 
      "requires_exact_match": true,
      "reason": "Sequential numbers are semantically identical",
      "extraction_pattern": "Numeric or prefixed (PO-XXXXX)"
    },
    {
      "field_name": "machine_name",
      "field_type": "enum",
      "requires_exact_match": true,
      "reason": "Similar machine names must be distinguished",
      "extraction_pattern": "Canonical machine name"
    }
  ]
}
```

### 2. STRUCTURED METADATA TAGS

Transform output includes explicit metadata tags for keyword matching:

```
[META: date=2025-12-03 | machine=CLIFFORD_MMW | product=IMG4-44-2015 | order=254980]

CLIFFORD MMW produced 800 units of IMG4-44-2015 on December 3, 2025. 
Achieved 994.0 units with 124.25% yield rate.
```

**Why this works:**
- `date=2025-12-03` is keyword-searchable and distinct from `date=2025-12-08`
- BM25/keyword search can exact-match on these tags
- Semantic search still works on the narrative text
- Hybrid search combines both

### 3. QUERY-TIME ENTITY EXTRACTION (Future Enhancement)

Before retrieval, extract entities from user query:
- "What was made on MMW on December 3?" → Extract: machine=MMW, date=December 3
- Convert to metadata filter: `date=2025-12-03 AND machine CONTAINS MMW`
- Apply filter + semantic search

### 4. IMPLEMENTATION STEPS

#### Step 1: Update analyze_file.txt prompt
Add section for "retrieval_sensitive_fields" detection

#### Step 2: Update transform.py
- Read retrieval_sensitive_fields from analysis
- Extract values from each record
- Generate [META: ...] tag line before each paragraph

#### Step 3: Update transform_v2.txt prompt  
- Add instructions to include metadata tags
- Show examples of proper tag formatting

#### Step 4: Test on sample files
- Transform 2-3 files
- Upload to RAGFlow
- Test date/code/order queries

#### Step 5: Full re-transform
- All 40+ files with new intelligent tagging
- ~2-3 hours

#### Step 6: Re-upload and rebuild KG
- Parse: ~5 mins
- KG: ~3-5 hours

### 5. EXPECTED OUTCOME

Query: "What products were made on MMW on December 3?"

Keyword search finds: `[META: date=2025-12-03 | machine=CLIFFORD_MMW]`
→ Exact match on date and machine
→ Correct chunk retrieved
→ Accurate answer: "IMG4-44-2015, 800 units"

### 6. FUTURE-PROOF DESIGN

The system is self-learning:
1. LLM analyzes new file schemas automatically
2. Detects which fields need exact matching
3. Generates appropriate tags dynamically
4. No hardcoding required for new data types

---

## Timeline

| Step | Duration | Notes |
|------|----------|-------|
| Update prompts & code | 1 hour | Design work |
| Test on 2-3 files | 30 mins | Validation |
| Full re-transform | 2-3 hours | Can run unattended |
| Re-upload & parse | 10 mins | |
| Rebuild KG | 3-5 hours | Can run overnight |
| Validation testing | 30 mins | |

**Total: ~8-10 hours (mostly unattended)**

---

## References

- [Anyscale: Exact-match and relational lookups](https://docs.anyscale.com/rag/quality-improvement/retrieval-strategies)
- [Superlinked: Hybrid Search & Reranking](https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking)
- [Shelf.io: Data Enrichment Strategies](https://shelf.io/blog/data-enrichment/)
- [Haystack: Automated Metadata Enrichment](https://haystack.deepset.ai/cookbook/metadata_enrichment)
