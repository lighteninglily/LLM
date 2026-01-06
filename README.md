# Local AI Server with RAG

A fully automated deployment tool for running a local AI server with RAG (Retrieval-Augmented Generation) capabilities. Uses vLLM for multi-GPU LLM inference and AnythingLLM for the RAG pipeline and web interface.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Server                               │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │   GPU 0 (4090)  │    │              vLLM                   │ │
│  │     24GB VRAM   │◄──►│   Tensor Parallel Inference         │ │
│  └─────────────────┘    │   OpenAI-compatible API (:8000)     │ │
│  ┌─────────────────┐    └─────────────────────────────────────┘ │
│  │   GPU 1 (4090)  │                    ▲                       │
│  │     24GB VRAM   │                    │                       │
│  └─────────────────┘                    ▼                       │
│                         ┌─────────────────────────────────────┐ │
│                         │          AnythingLLM               │ │
│                         │   • Document Ingestion              │ │
│                         │   • Vector Database (LanceDB)       │ │
│                         │   • RAG Pipeline                    │ │
│                         │   • Web UI (:3001)                  │ │
│                         └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Requirements

- **OS**: Ubuntu 22.04 / 24.04 LTS **OR** Windows 10/11 with **WSL2** (Ubuntu instance)
- **GPU**: NVIDIA RTX 5090 (32GB), RTX 4090 (24GB), or 2x RTX 4090 (48GB)
- **RAM**: 64GB+ recommended
- **Storage**: 100GB+ free space (for models)
- **Network**: Internet connection for initial setup

## Quick Start

### 1. Get the deployment tool

```bash
# Clone this repository
git clone https://github.com/lightninglily/LLM.git
cd LLM

# Or just download deploy.py directly
wget https://raw.githubusercontent.com/lightninglily/LLM/main/deploy.py
```

### 2. Run hardware detection

```bash
python3 deploy.py detect
```

- **Windows Users**: Run this inside your WSL2 terminal. The script will detect your Windows-managed GPUs automatically.

### 3. Run the installer

```bash
python3 deploy.py install
```

### 4. Configure HuggingFace token

For gated models like Llama-2, you need a HuggingFace token:

1. Get token from: https://huggingface.co/settings/tokens
2. Accept model license at: https://huggingface.co/meta-llama/Llama-2-70b-chat-hf
3. Add token to config:

```bash
nano ~/.local-ai-server/.env
# Add: HF_TOKEN=hf_xxxxxxxxxx
```

### 5. Start the server

```bash
cd ~/.local-ai-server
./start.sh
```

First startup takes 10-30 minutes to download the model (~35GB for 70B-AWQ).

### 6. Access the UI

- **AnythingLLM UI**: http://localhost:3001
- **vLLM API**: http://localhost:8000/v1

**Note**: Authentication is ENABLED by default. On first visit to AnythingLLM, you will be asked to create an admin account.

## Management Commands

```bash
# Start services
~/.local-ai-server/start.sh

# Stop services
~/.local-ai-server/stop.sh

# Check status
~/.local-ai-server/status.sh

# View logs
~/.local-ai-server/logs.sh

# View specific service logs
docker compose logs -f vllm
docker compose logs -f anythingllm
```

## Configuration

Edit `~/.local-ai-server/config.json`:

```json
{
  "llm": {
    "model": "TheBloke/Llama-2-70B-Chat-AWQ",
    "backend": "vllm",
    "tensor_parallel_size": 2,
    "max_model_len": 4096,
    "gpu_memory_utilization": 0.85,
    "quantization": "awq"
  },
  "embedding": {
    "model": "BAAI/bge-large-en-v1.5",
    "device": "cpu"
  },
  "server": {
    "vllm_host": "0.0.0.0",
    "vllm_port": 8000,
    "anythingllm_port": 3001
  }
}
```

After changing config, regenerate docker-compose:
```bash
python3 deploy.py install  # Just re-run, it will update
```

## Recommended Models (2026)

### For 1x RTX 5090 (32GB VRAM)

| Model | Size | VRAM Usage | Quality | Speed |
|-------|------|------------|---------|-------|
| Qwen3-32B-Instruct | ~18GB | ~22GB | ⭐⭐⭐⭐⭐ | Fast |
| Gemma-3-27B | ~15GB | ~18GB | ⭐⭐⭐⭐⭐ | Very Fast |
| Llama-3.3-70B-AWQ | ~37GB | ~30GB | ⭐⭐⭐⭐⭐ | Medium |
| Qwen3-Coder-32B | ~18GB | ~22GB | ⭐⭐⭐⭐⭐ (coding) | Fast |

### For 1x RTX 4090 (24GB VRAM)

| Model | Size | VRAM Usage | Quality |
|-------|------|------------|---------|
| Qwen3-14B-Instruct | ~8GB | ~11GB | ⭐⭐⭐⭐ |
| Gemma-3-12B | ~7GB | ~9GB | ⭐⭐⭐⭐ |
| Qwen3-8B-Instruct | ~5GB | ~7GB | ⭐⭐⭐⭐ |

To change models, edit `config.json` and update the model path:
```json
{
  "llm": {
    "model": "Qwen/Qwen3-32B-Instruct"
  }
}
```

## Using AnythingLLM

### First-time Setup

1. Open http://localhost:3001
2. **Create an Admin Account**: You will be prompted to set up a username and password.
3. The LLM provider is pre-configured to use vLLM.

### Adding Documents (RAG)

1. Click "Workspaces" → Create new workspace
2. Click the upload icon
3. Drag and drop documents (PDF, DOCX, TXT, etc.)
4. Click "Move to Workspace" to process them
5. Start chatting with your documents!

### Supported Document Types

- PDF
- Word documents (.docx)
- Text files (.txt, .md)
- Web pages (paste URL)
- YouTube transcripts
- And more...

## API Usage

vLLM exposes an OpenAI-compatible API:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="YOUR_VLLM_API_KEY"  # Check ~/.local-ai-server/.env
)

response = client.chat.completions.create(
    model="TheBloke/Llama-2-70B-Chat-AWQ",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
print(response.choices[0].message.content)
```

Or with curl:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "TheBloke/Llama-2-70B-Chat-AWQ",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Troubleshooting

### vLLM won't start / OOM errors

1. Check GPU memory:
```bash
nvidia-smi
```

2. Reduce context length in config:
```json
{
  "llm": {
    "max_model_len": 2048
  }
}
```

3. Try a smaller model

### Model download fails

1. Check HuggingFace token is set
2. Accept model license on HuggingFace website
3. Check disk space: `df -h`

### Services not connecting

1. Check if containers are running:
```bash
docker compose ps
```

2. Check logs:
```bash
docker compose logs vllm
docker compose logs anythingllm
```

3. Verify network:
```bash
docker network inspect local-ai-network
```

### GPU not detected in Docker

1. Verify NVIDIA Container Toolkit:
```bash
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

2. If fails, reinstall (Ubuntu only - WSL manages this differently):
```bash
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## Updating

### Update AnythingLLM

```bash
cd ~/.local-ai-server
docker compose pull anythingllm
docker compose up -d anythingllm
```

### Update vLLM

```bash
cd ~/.local-ai-server
docker compose pull vllm
docker compose up -d vllm
```

### Update Everything

```bash
cd ~/.local-ai-server
docker compose pull
docker compose up -d
```

## Uninstall

```bash
# Stop services
~/.local-ai-server/stop.sh

# Remove containers and volumes
cd ~/.local-ai-server
docker compose down -v

# Remove installation
rm -rf ~/.local-ai-server
```

## Security Notes

1. **Authentication**: Enabled by default (`PASSWORDLESS_AUTH=false`). You must create an account on first login.
2. **Network**: Services bind to `0.0.0.0` by default. For production, restrict ports 3001 and 8000 to trusted IPs or use a reverse proxy.
3. **HTTPS**: Put behind a reverse proxy (nginx/traefik) with SSL for secure remote access.

## Credits

This project combines:
- [vLLM](https://github.com/vllm-project/vllm) - High-throughput LLM serving
- [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm) - RAG and UI
- [HuggingFace](https://huggingface.co) - Model repository

## License

MIT License - See LICENSE file
