# RAG & Knowledge Graph Improvements - TODO

*Research conducted: 2026-01-28*

## What We May Not Know (Key Findings)

### 1. Chunking Strategy Issues

| Current | Best Practice |
|---------|---------------|
| Fixed 128 tokens | **512 tokens + 50-100 token overlap** recommended as baseline |
| No overlap | Overlap preserves context at boundaries |
| Generic chunking | **Semantic chunking** (meaning-based) better for dense data |

**"Lost in the Middle" Effect:** LLMs struggle with info buried in middle of long contexts. Smaller, focused chunks = better retrieval accuracy.

---

### 2. Advanced Chunking Techniques We're NOT Using

- **Semantic Chunking**: Splits by meaning, not character count. Groups sentences by embedding similarity.
- **LLM-Based Chunking**: Uses LLM to decide chunk boundaries (expensive but highest quality)
- **Agentic Chunking**: AI agent dynamically chooses best strategy per document

---

### 3. Entity Extraction Post-Processing (Critical Gap)

Neo4j's approach includes **post-processing steps we're missing**:
- **Entity merging**: Combining duplicate/related entities
- **Graph optimization**: Refining relationships after extraction
- **HAS_ENTITY linking**: Each entity links back to source chunk

---

### 4. GraphRAG vs Traditional RAG

| Traditional RAG | GraphRAG |
|-----------------|----------|
| Single-hop retrieval | **Multi-hop reasoning** |
| Isolated text chunks | Connected entities + relationships |
| Simple Q&A | Complex relational queries |
| "What is X?" | "How does X connect to Y through Z?" |

**RAGFlow uses Knowledge Graph** - we're on the right track, but need better entity/relationship quality.

---

### 5. Key Challenges Identified

1. **Data Integration**: Our files have different schemas - per-file analysis addresses this ✅
2. **Entity Consistency**: Same entity with different names → we have `entity_normalizer.py` ✅
3. **Relationship Extraction**: Need explicit relationship phrases → we added this ✅
4. **Schema Inference**: LLM should dynamically infer schema → per-file analysis does this ✅

---

## Potential Improvements to Consider (After Current Run)

| Area | Current | Potential Upgrade | Priority |
|------|---------|-------------------|----------|
| **Chunk size** | 128 tokens | Try 256-512 with overlap | High |
| **Chunk overlap** | None | Add 50-100 token overlap | High |
| **Post-processing** | None | Add entity deduplication/merging | Medium |
| **Hybrid retrieval** | Vector only | Vector + graph traversal | Low |
| **Semantic chunking** | Fixed | Meaning-based segmentation | Medium |

---

## What We're Doing Right ✅

1. **Per-file analysis** - tailors extraction to each schema
2. **Entity normalization** - consistent naming
3. **Relationship phrase templates** - explicit connections
4. **Source context preservation** - traceability
5. **Using Knowledge Graph** - not just vector search

---

## Action Items

- [ ] Complete current pipeline run
- [ ] Evaluate KG quality in RAGFlow UI
- [ ] If quality issues, consider increasing chunk size to 256-512
- [ ] Add chunk overlap (50-100 tokens)
- [ ] Implement post-processing entity deduplication
- [ ] Test with sample queries to measure improvement

---

## References

- [Weaviate Chunking Strategies](https://weaviate.io/blog/chunking-strategies-for-rag)
- [Neo4j KG Extraction Challenges](https://neo4j.com/blog/developer/knowledge-graph-extraction-challenges/)
- [DataCamp KG RAG Tutorial](https://www.datacamp.com/tutorial/knowledge-graph-rag)
- [Graph RAG vs RAG](https://datasciencedojo.com/blog/graph-rag-vs-rag/)
