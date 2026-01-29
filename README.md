# RAGFlow Automation Toolkit

Automatically ingest ANY dataset into RAGFlow with optimal Knowledge Graph configuration.

## Quick Start

```bash
python main.py --input /path/to/data --name "My Dataset"
```

## Prerequisites

### vLLM Configuration (CRITICAL)

vLLM must have 64K context enabled for KG to work:

```yaml
# In docker-compose.yml
environment:
  - VLLM_ALLOW_LONG_MAX_MODEL_LEN=1
  - MAX_MODEL_LEN=65536
```

### Services Required

- **vLLM**: Running at `http://localhost:8000`
- **RAGFlow**: Running at `http://localhost:9380`
- **Ollama**: Running at `http://localhost:11434` (for embeddings)

## Usage

### End-to-End (Recommended)

```bash
python main.py --input /path/to/data --name "My Dataset"
```

### Step-by-Step

```bash
# Step 1: Analyze data structure
python analyze.py --input /path/to/data

# Step 2: Transform data (if needed)
python transform.py --input /path/to/data --output ./output

# Step 3: Setup RAGFlow KB with KG
python setup_ragflow.py --data ./output --name "My Dataset"
```

### Options

| Flag | Description |
|------|-------------|
| `--input` | Path to source data folder (required) |
| `--name` | Knowledge Base name (required) |
| `--output` | Transform output directory (default: `./output`) |
| `--analyze-only` | Run only analysis step |
| `--skip-transform` | Skip transformation, use input directly |
| `--skip-kg` | Create KB without KG generation |
| `--verbose` | Show detailed LLM prompts/responses |

## Configuration

Edit `config/settings.yaml` to customize:

- LLM endpoints and models
- RAGFlow API key
- Batch sizes and parallelism
- KG optimization settings

## File Splitting

Large files are automatically split to prevent KG performance issues:
- Max 500 records per output file
- Each file becomes ~500 chunks in RAGFlow
- Prevents multi-hour single-document KG processing

## Hardware Profiles

### RTX 5080 (Current)
- batch_size: 20
- parallel_calls: 2

### RTX 5090 (Future)
Change `hardware_profile: "5090"` in settings.yaml for:
- batch_size: 50
- parallel_calls: 4

## Logs

All operations logged to `logs/` folder with timestamps.
