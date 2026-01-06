# RTX 5090 Deployment Guide - Local AI Server (2026)

## Overview

This guide covers deploying a local LLM server on Ubuntu 24.04 with NVIDIA RTX 5090 (32GB VRAM), optimized for 2026 models.

## Hardware Specs

- **GPU**: NVIDIA RTX 5090 (32GB GDDR7)
- **CPU**: Intel Core Ultra 7 265KF
- **RAM**: 64GB DDR5 6000MHz
- **Storage**: 2x 2TB NVMe SSD
- **OS**: Ubuntu 24.04 LTS

## Quick Start (5 Steps)

### 1. Install Ubuntu 24.04

Fresh install recommended. Enable OpenSSH during installation if you want remote access.

### 2. Run Installation Script

```bash
# Download and run the installer
wget https://raw.githubusercontent.com/lightninglily/LLM/main/install-ubuntu-rtx5090.sh
chmod +x install-ubuntu-rtx5090.sh
./install-ubuntu-rtx5090.sh
```

The script will:
- Update system packages
- Install NVIDIA drivers (550+)
- Install Docker + NVIDIA Container Toolkit
- Set up the AI server
- Reboot if needed

### 3. Configure HuggingFace Token

```bash
nano ~/.local-ai-server/.env
```

Add your token:
```bash
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxx
```

Get token from: https://huggingface.co/settings/tokens

For gated models (Llama), accept the license on the model page.

### 4. Start the Server

```bash
~/.local-ai-server/start.sh
```

First startup takes 10-20 minutes to download the model.

### 5. Access the UI

Open browser: http://localhost:3001

Create admin account on first login.

## Recommended Models (2026)

### Best Overall: Qwen3-32B-Instruct
- **VRAM**: ~22GB
- **Speed**: Fast (5000+ tokens/sec on RTX 5090)
- **Quality**: SOTA 2026, excellent reasoning
- **Context**: 128k tokens
- **Use**: General purpose, reasoning, multilingual

```bash
# Already configured as default
LLM_MODEL=Qwen/Qwen3-32B-Instruct
```

### Fastest: Gemma-3-27B
- **VRAM**: ~18GB
- **Speed**: Very Fast (6500+ tokens/sec)
- **Quality**: Excellent
- **Context**: 8k tokens
- **Use**: General purpose, high throughput

```bash
LLM_MODEL=google/gemma-3-27b
```

### Best Coding: Qwen3-Coder-32B
- **VRAM**: ~22GB
- **Speed**: Fast
- **Quality**: SOTA coding 2026
- **Use**: Code generation, debugging, SWE agents

```bash
LLM_MODEL=Qwen/Qwen3-Coder-32B
```

### Maximum Quality: Llama-3.3-70B (tight fit)
- **VRAM**: ~30GB (uses most of 32GB)
- **Speed**: Medium (3000+ tokens/sec)
- **Quality**: Highest
- **Context**: 128k tokens
- **Use**: Complex reasoning, high-quality output

```bash
LLM_MODEL=casperhansen/llama-3.3-70b-instruct-awq
```

## Changing Models

### Method 1: Edit .env file

```bash
nano ~/.local-ai-server/.env
```

Change:
```bash
LLM_MODEL=Qwen/Qwen3-32B-Instruct
LLM_MODEL_NAME=Qwen3-32B-Instruct
```

Restart:
```bash
~/.local-ai-server/stop.sh
~/.local-ai-server/start.sh
```

### Method 2: Interactive selection

```bash
cd ~/local-ai-server
python3 models.py list --gpus 1 --vram 32
python3 models.py select --gpus 1 --vram 32
```

## Performance Expectations

RTX 5090 performance (based on benchmarks):

| Model Size | Tokens/sec | Concurrent Users |
|-----------|-----------|------------------|
| 4B-8B | 15,000+ | 100+ |
| 14B-32B | 5,000+ | 30+ |
| 70B | 3,000+ | 10+ |

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

# Monitor GPU
watch -n 1 nvidia-smi
```

## API Usage

### Python

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="Qwen/Qwen3-32B-Instruct",
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
)
print(response.choices[0].message.content)
```

### curl

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-32B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## RAG (Document Upload)

1. Open http://localhost:3001
2. Create a workspace
3. Click upload icon
4. Drag and drop PDFs, DOCX, TXT, etc.
5. Chat with your documents

Supported formats: PDF, DOCX, TXT, MD, CSV, JSON, web pages, YouTube transcripts

## Troubleshooting

### Model won't load / OOM errors

1. Check VRAM usage: `nvidia-smi`
2. Try smaller model or reduce context:
   ```bash
   nano ~/.local-ai-server/.env
   MAX_MODEL_LEN=2048
   GPU_MEMORY_UTIL=0.80
   ```
3. Restart services

### Slow performance

1. Ensure no other processes using GPU
2. Check temperature: `nvidia-smi -q -d TEMPERATURE`
3. Disable `--enforce-eager` in docker-compose.yml (already removed in 2026 config)

### Docker can't access GPU

```bash
# Verify Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# If fails, reconfigure
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Connection refused

```bash
# Check container status
docker compose ps

# View logs
docker compose logs vllm
docker compose logs anythingllm
```

## Advanced: Multiple Models

Run multiple models on the same GPU (if VRAM allows):

```bash
# Terminal 1: Start Qwen3-32B on port 8000
docker run --gpus all -p 8000:8000 vllm/vllm-openai:latest \
  --model Qwen/Qwen3-32B-Instruct

# Terminal 2: Start Qwen3-8B on port 8001
docker run --gpus all -p 8001:8000 vllm/vllm-openai:latest \
  --model Qwen/Qwen3-8B-Instruct
```

## Upgrading

```bash
cd ~/.local-ai-server
docker compose pull
docker compose down
docker compose up -d
```

## System Monitoring

```bash
# GPU usage
watch -n 1 nvidia-smi

# Detailed GPU stats
nvidia-smi dmon

# Container stats
docker stats

# Service logs (live)
docker compose logs -f
```

## Security Recommendations

1. **Authentication**: Already enabled by default (PASSWORDLESS_AUTH=false)
2. **Firewall**: Only allow localhost or trusted IPs
   ```bash
   sudo ufw allow from 192.168.1.0/24 to any port 3001
   sudo ufw allow from 192.168.1.0/24 to any port 8000
   ```
3. **HTTPS**: Use reverse proxy (nginx) with SSL for remote access
4. **Updates**: Keep system and containers updated

## Backup

```bash
# Backup configuration and data
tar -czf ~/ai-server-backup.tar.gz ~/.local-ai-server/
```

## Support

- Check logs: `~/.local-ai-server/logs.sh`
- Test API: `python3 ~/local-ai-server/test_server.py`
- GPU info: `nvidia-smi -q`
- System info: `python3 ~/local-ai-server/deploy.py detect`

## What's New in 2026

- **Qwen3** models: Best reasoning, multilingual
- **Gemma 3**: Google's latest, highly efficient
- **Llama 3.3**: Meta's improved 70B
- **RTX 5090**: 2.6x faster than A100 for inference
- **Better quantization**: AWQ optimizations for Blackwell architecture
