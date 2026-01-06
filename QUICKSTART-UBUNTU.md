# Quick Start Guide - Ubuntu 24.04 + RTX 5090

## Once Ubuntu is Installed

### Step 1: Download Installation Script

```bash
cd ~
wget https://raw.githubusercontent.com/lightninglily/LLM/main/install-ubuntu-rtx5090.sh
chmod +x install-ubuntu-rtx5090.sh
```

### Step 2: Run Installation Script

```bash
./install-ubuntu-rtx5090.sh
```

**What it does:**
- Updates Ubuntu packages
- Installs NVIDIA drivers (550+)
- Installs Docker
- Installs NVIDIA Container Toolkit
- Sets up the AI server
- Tests GPU access

**Time required:** 60-90 minutes (includes reboot)

**Note:** Script will reboot if drivers need to be installed. Run it again after reboot.

### Step 3: Configure HuggingFace Token (Optional)

Only needed for gated models like Llama. Qwen3-32B (default) doesn't require this.

```bash
nano ~/.local-ai-server/.env
```

Add your token:
```bash
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxx
```

Save: `Ctrl+X`, then `Y`, then `Enter`

Get token from: https://huggingface.co/settings/tokens

### Step 4: Start the Server

```bash
~/.local-ai-server/start.sh
```

**First run:** Downloads Qwen3-32B model (~18GB, takes 10-20 minutes)

**Watch progress:**
```bash
docker compose logs -f vllm
```

Exit logs: `Ctrl+C`

### Step 5: Access the UI

Open browser: **http://localhost:3001**

Create admin account on first login.

---

## Verify Everything Works

```bash
# Check GPU is detected
nvidia-smi

# Check containers are running
docker compose ps

# Check service health
~/.local-ai-server/status.sh

# Run test suite
cd ~/local-ai-server
python3 test_server.py
```

---

## Common Commands

```bash
# Start server
~/.local-ai-server/start.sh

# Stop server
~/.local-ai-server/stop.sh

# View logs
~/.local-ai-server/logs.sh

# Check status
~/.local-ai-server/status.sh

# Monitor GPU
watch -n 1 nvidia-smi
```

---

## What Gets Installed

- **Model:** Qwen3-32B-Instruct (18GB, SOTA 2026)
- **UI:** AnythingLLM (RAG + document chat)
- **API:** vLLM OpenAI-compatible server on port 8000
- **Location:** ~/.local-ai-server/

---

## Change Model Later

```bash
# List compatible models
cd ~/local-ai-server
python3 models.py list --gpus 1 --vram 32

# Interactive selection
python3 models.py select --gpus 1 --vram 32

# Manual edit
nano ~/.local-ai-server/.env
# Change: LLM_MODEL=Qwen/Qwen3-32B-Instruct
# To: LLM_MODEL=google/gemma-3-27b

# Restart
~/.local-ai-server/stop.sh
~/.local-ai-server/start.sh
```

---

## Troubleshooting

**Script fails:**
```bash
# Check Ubuntu version
lsb_release -a

# Check for GPU
lspci | grep -i nvidia

# Run script with verbose output
bash -x install-ubuntu-rtx5090.sh
```

**Docker can't access GPU:**
```bash
# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# If fails, reconfigure
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

**Model download is slow:**
```bash
# Check download progress
docker compose logs -f vllm | grep -i download
```

**Out of memory errors:**
```bash
# Edit config to use less memory
nano ~/.local-ai-server/.env
# Change: GPU_MEMORY_UTIL=0.85
# To: GPU_MEMORY_UTIL=0.75

# Or use smaller model
# Change: LLM_MODEL=Qwen/Qwen3-32B-Instruct
# To: LLM_MODEL=Qwen/Qwen3-14B-Instruct
```

---

## Need More Help?

See full guide: `DEPLOYMENT-GUIDE-RTX5090.md`

Check logs:
```bash
~/.local-ai-server/logs.sh
```

System info:
```bash
cd ~/local-ai-server
python3 deploy.py detect
```
