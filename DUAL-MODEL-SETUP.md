# Dual-Model Setup Guide

## Overview

This configuration runs **TWO AI models simultaneously** on your single RTX 5090:

- **Qwen3-32B-Instruct** - Text-only model (faster, better reasoning)
- **Qwen2.5-VL-32B-Instruct** - Vision + text model (image understanding)

Both models run side-by-side, allowing you to choose the right model for each task.

---

## Why Dual Models?

### Use the Right Tool for the Job:

**Text Model (Qwen3-32B)** - Best for:
- ✅ Pure text analysis and reasoning
- ✅ Document RAG (faster retrieval + generation)
- ✅ Code generation
- ✅ Long-form writing
- ✅ Math and logic problems
- ✅ Data analysis without images

**Vision Model (Qwen2.5-VL)** - Best for:
- ✅ Image description and understanding
- ✅ OCR (printed and handwritten)
- ✅ Chart/graph reading from images
- ✅ Invoice/receipt data extraction
- ✅ Visual reasoning
- ✅ Screenshot analysis
- ✅ Multi-modal conversations (text + images)

---

## Resource Usage

### VRAM Allocation:

```
Total GPU Memory:    32GB (RTX 5090)

Qwen3-32B:          ~12GB (38% allocation)
Qwen2.5-VL:         ~12GB (38% allocation)
Overhead:           ~3GB  (Docker, system)
──────────────────────────────────────────
Total Used:         ~27GB
Free Buffer:        ~5GB
```

### Configuration:

Both models run with:
- `--gpu-memory-utilization=0.38` (38% each = 76% total)
- Reduced context windows for memory efficiency
  - Text model: 6K tokens
  - Vision model: 4K tokens
- Shared GPU but isolated memory spaces

---

## Installation

### Prerequisites:

- RTX 5090 (or similar 32GB+ GPU)
- Ubuntu 24.04 LTS
- NVIDIA drivers 550+
- Docker + NVIDIA Container Toolkit

### Quick Start:

```bash
cd ~/.local-ai-server

# Start both models
./start-dual-model.sh

# Wait 5-10 minutes for models to load
# First run downloads both models (~38GB total)

# Access interfaces
firefox http://localhost:3000  # Open WebUI - select model
```

---

## Interface Configuration

### Open WebUI - User Selects Model

**Best experience for switching between models:**

1. Open http://localhost:3000
2. Create account / login
3. Click model dropdown at top
4. See both models:
   - `Qwen/Qwen3-32B-Instruct` (Text)
   - `Qwen/Qwen2.5-VL-32B-Instruct` (Vision)
5. Select based on task:
   - Text-only question? → Qwen3-32B (faster)
   - Have an image? → Qwen2.5-VL

**Features:**
- Switch models mid-conversation
- Upload images (only works with VL model)
- Both models share same API key
- Chat history preserved per model

---

### AnythingLLM - Always Text Model

**Optimized for document RAG:**

- Fixed to Qwen3-32B (text model)
- Best performance for RAG workloads
- No vision needed for text documents
- Fastest vector search + generation

Configuration in `docker-compose.enhanced-dual.yml`:
```yaml
anythingllm:
  environment:
    - OPEN_AI_BASE_URL=http://vllm-text:8000/v1
    - OPEN_AI_MODEL=Qwen/Qwen3-32B-Instruct
```

---

### JupyterLab - Both Models Available

**Programmatic access to both:**

```python
from openai import OpenAI

# Text model client
text_client = OpenAI(
    base_url="http://vllm-text:8000/v1",
    api_key="dummy"
)

# Vision model client
vision_client = OpenAI(
    base_url="http://vllm-vision:8000/v1",
    api_key="dummy"
)

# Use appropriate client based on task
def analyze_data(file_path, question):
    if file_path.endswith(('.png', '.jpg', '.jpeg')):
        # Use vision model for images
        return vision_client.chat.completions.create(...)
    else:
        # Use text model for CSVs, text files
        return text_client.chat.completions.create(...)
```

**Example - Image Analysis:**

```python
import base64

# Read image
with open("chart.png", "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode()

# Send to vision model
response = vision_client.chat.completions.create(
    model="Qwen/Qwen2.5-VL-32B-Instruct",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Extract all data from this chart"},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}"
                }
            }
        ]
    }],
    max_tokens=1000
)

print(response.choices[0].message.content)
```

---

### Direct API Access

**Both models have separate endpoints:**

```bash
# Text model
curl http://localhost:8000/v1/models

# Vision model
curl http://localhost:8001/v1/models
```

**Chat completion example:**

```python
import requests

# Text model (faster for pure text)
text_response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    json={
        "model": "Qwen/Qwen3-32B-Instruct",
        "messages": [{"role": "user", "content": "Explain quantum computing"}],
        "max_tokens": 500
    }
)

# Vision model (for images)
vision_response = requests.post(
    "http://localhost:8001/v1/chat/completions",
    json={
        "model": "Qwen/Qwen2.5-VL-32B-Instruct",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image"},
                {"type": "image_url", "image_url": {"url": "data:image/..."}}
            ]
        }],
        "max_tokens": 500
    }
)
```

---

## Use Case Examples

### Example 1: Invoice Processing (Vision Model)

```python
# Upload invoice photo
with open("invoice.jpg", "rb") as f:
    img_data = base64.b64encode(f.read()).decode()

response = vision_client.chat.completions.create(
    model="Qwen/Qwen2.5-VL-32B-Instruct",
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Extract: vendor, date, total, line items"
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}
            }
        ]
    }]
)

# Get structured data
invoice_data = response.choices[0].message.content
```

### Example 2: Financial Analysis (Text Model)

```python
# Analyze CSV data - use faster text model
import pandas as pd

df = pd.read_csv("sales_data.csv")

response = text_client.chat.completions.create(
    model="Qwen/Qwen3-32B-Instruct",
    messages=[{
        "role": "user",
        "content": f"Analyze this data and provide insights:\n{df.to_string()}"
    }]
)

print(response.choices[0].message.content)
```

### Example 3: Chart Reading (Vision Model)

```python
# Read data from chart image
with open("sales_chart.png", "rb") as f:
    img_data = base64.b64encode(f.read()).decode()

response = vision_client.chat.completions.create(
    model="Qwen/Qwen2.5-VL-32B-Instruct",
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Extract exact numbers from this chart. Return as CSV."
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_data}"}
            }
        ]
    }]
)

# Get structured data
csv_data = response.choices[0].message.content
```

---

## Monitoring & Management

### Check VRAM Usage:

```bash
# Single check
./check-vram-usage.sh

# Continuous monitoring
./check-vram-usage.sh --watch
```

**Output shows:**
- Total/used/free VRAM
- Running container status
- GPU process details
- Recommendations if usage high

### View Logs:

```bash
# All services
docker compose -f docker-compose.enhanced-dual.yml logs -f

# Specific service
docker logs -f vllm-text
docker logs -f vllm-vision
docker logs -f open-webui
```

### Restart Services:

```bash
# Restart everything
docker compose -f docker-compose.enhanced-dual.yml restart

# Restart specific service
docker restart vllm-text
docker restart vllm-vision
```

### Stop Services:

```bash
./stop-dual-model.sh
```

---

## Performance Tuning

### If You Experience OOM (Out of Memory):

**Option 1: Reduce GPU memory allocation**

Edit `docker-compose.enhanced-dual.yml`:

```yaml
vllm-text:
  command:
    - --gpu-memory-utilization=0.35  # Reduce from 0.38

vllm-vision:
  command:
    - --gpu-memory-utilization=0.35  # Reduce from 0.38
```

**Option 2: Reduce context windows**

```yaml
vllm-text:
  command:
    - --max-model-len=4096  # Reduce from 6144

vllm-vision:
  command:
    - --max-model-len=3072  # Reduce from 4096
```

**Option 3: Use quantized models**

Replace models with AWQ versions:
- `Qwen/Qwen3-32B-Instruct-AWQ`
- Check HuggingFace for VL AWQ version

### If One Model is Slow:

**Increase allocation for frequently used model:**

```yaml
vllm-text:
  command:
    - --gpu-memory-utilization=0.45  # Increase if used more

vllm-vision:
  command:
    - --gpu-memory-utilization=0.30  # Decrease if used less
```

---

## Troubleshooting

### Both Models Won't Start:

```bash
# Check VRAM availability
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# View startup logs
docker logs vllm-text
docker logs vllm-vision
```

### Open WebUI Doesn't Show Both Models:

1. Verify both vLLM containers healthy:
   ```bash
   curl http://localhost:8000/v1/models
   curl http://localhost:8001/v1/models
   ```

2. Check Open WebUI environment:
   ```bash
   docker exec open-webui env | grep OPENAI
   ```

3. Restart Open WebUI:
   ```bash
   docker restart open-webui
   ```

### Vision Model Can't See Images:

- Ensure using vision model endpoint (`:8001`)
- Image must be base64 encoded in message
- Check image format supported (PNG, JPEG, WebP)
- Verify `image_url` structure in API call

### Performance Issues:

```bash
# Check VRAM usage
./check-vram-usage.sh

# Check if swapping
free -h

# Monitor GPU utilization
nvidia-smi dmon -s u
```

---

## Migration from Single Model

### From `docker-compose.enhanced.yml`:

```bash
# Stop single-model setup
docker compose -f docker-compose.enhanced.yml down

# Start dual-model setup
./start-dual-model.sh
```

**What's preserved:**
- ✅ All AnythingLLM data (workspaces, vectors)
- ✅ All Jupyter notebooks
- ✅ All uploaded documents
- ✅ Open WebUI will be new (create new account)

**What changes:**
- Model selection now available in Open WebUI
- Two vLLM endpoints (`:8000` and `:8001`)
- Slightly reduced context windows

---

## FAQ

**Q: Can I run just one model?**
A: Yes, use `docker-compose.enhanced.yml` for single model setup.

**Q: Which model should I use for RAG?**
A: Text model (Qwen3-32B) - faster and better for pure text.

**Q: Can the vision model also do text?**
A: Yes, but it's slower. Use text model when no images involved.

**Q: How much slower is vision model?**
A: ~20-30% slower for pure text, similar speed when processing images.

**Q: Can I use different models?**
A: Yes, edit `docker-compose.enhanced-dual.yml` and change model names.

**Q: What if I have more/less VRAM?**
A: Adjust `--gpu-memory-utilization` values proportionally.

**Q: Can I run this on multiple GPUs?**
A: Yes, assign each model to different GPU with `device_ids: ['0']` and `['1']`.

---

## Summary

**Dual-model setup gives you:**
- ✅ Best of both worlds (text speed + vision capability)
- ✅ User selects appropriate model per task
- ✅ Optimized performance for each use case
- ✅ Single GPU handles both models
- ✅ No manual switching required
- ✅ All interfaces fully functional

**Perfect for:**
- Business with mixed workloads
- Invoice/document processing + data analysis
- Screenshot analysis + text reasoning
- Any scenario needing both text and vision AI

---

## Support

**Issues?**
1. Check VRAM: `./check-vram-usage.sh`
2. View logs: `docker compose -f docker-compose.enhanced-dual.yml logs`
3. See `README.md` for general troubleshooting

**GitHub:** https://github.com/lightninglily/LLM
