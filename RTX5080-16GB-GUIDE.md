# RTX 5080 16GB Configuration Guide

Complete guide for running the Local AI Server on NVIDIA RTX 5080 with 16GB VRAM.

---

## VRAM Constraint Overview

**RTX 5080 vs RTX 5090:**

| GPU | VRAM | Best Config |
|-----|------|-------------|
| RTX 5090 | 32GB | 32B models, dual 32B, tri-model |
| RTX 5080 | 16GB | 14B models, dual 7B models |

**With 16GB, you need to use smaller models or quantized versions.**

---

## Recommended Configurations

### Option 1: Single 14B Model (Best Quality) ✅

**Best for: Maximum intelligence in single model**

```bash
# Use docker-compose.rtx5080-16gb.yml
docker compose -f docker-compose.rtx5080-16gb.yml up -d
```

**Specifications:**
- **Model**: Qwen2.5-14B-Instruct
- **VRAM Usage**: ~13GB (85% utilization)
- **Context**: 16K tokens
- **Performance**: Excellent quality, good speed

**Why 14B?**
- ✅ Best quality that fits in 16GB
- ✅ Better than 7B models
- ✅ Leaves room for large contexts
- ✅ Fast inference on RTX 5080

---

### Option 2: Dual 7B Models (Text + Vision) 🎯

**Best for: Image understanding + text**

```bash
# Use docker-compose.rtx5080-dual.yml
docker compose -f docker-compose.rtx5080-dual.yml up -d
```

**Specifications:**
- **Text Model**: Qwen2.5-7B-Instruct (~7GB)
- **Vision Model**: Qwen2.5-VL-7B-Instruct (~7GB)
- **Total VRAM**: ~14GB (88% utilization)
- **Context**: 8K text, 4K vision

**Trade-offs:**
- ✅ Image understanding capability
- ✅ Model selection per task
- ⚠️ Slightly lower quality than 14B
- ✅ Still very capable models

---

### Option 3: Single 7B Model (Maximum Speed) ⚡

**Best for: Speed, low latency**

```yaml
# Modify docker-compose.rtx5080-16gb.yml
vllm:
  command:
    - --model
    - Qwen/Qwen2.5-7B-Instruct
    - --gpu-memory-utilization=0.70
    - --max-model-len=32768  # Longer context possible
```

**Advantages:**
- ✅ Fastest inference
- ✅ Lower VRAM usage (~5-6GB)
- ✅ Room for very long context (32K)
- ⚠️ Lower quality than 14B

---

## VRAM Allocation Guide

### Understanding 16GB Limits:

**Model Size Estimates:**

| Model | Parameters | VRAM (FP16) | With Context |
|-------|-----------|-------------|--------------|
| 7B | 7 billion | ~4-5GB | ~6-7GB |
| 14B | 14 billion | ~10-11GB | ~13-14GB |
| 32B | 32 billion | ~20-22GB | ❌ Too large |

**Safe Configurations:**

```
16GB Total VRAM:
├─ Single 14B model: ~13GB ✅ (3GB buffer)
├─ Dual 7B models: ~14GB ✅ (2GB buffer)
├─ Single 32B model: ~22GB ❌ (exceeds VRAM)
└─ Dual 14B models: ~26GB ❌ (exceeds VRAM)
```

---

## Installation Steps

### Quick Start (14B Single Model):

```bash
# 1. Install Ubuntu and dependencies
./one-click-install.sh

# 2. Stop default setup
cd ~/.local-ai-server
./stop.sh

# 3. Download RTX 5080 config
wget https://raw.githubusercontent.com/lightninglily/LLM/main/local-ai-server/docker-compose.rtx5080-16gb.yml

# 4. Start with RTX 5080 config
docker compose -f docker-compose.rtx5080-16gb.yml up -d

# 5. Monitor startup
docker logs -f vllm
```

**First startup: ~10-15 minutes** (downloads 14B model ~8GB)

---

### Dual Model Setup (Text + Vision):

```bash
# Download dual config
wget https://raw.githubusercontent.com/lightninglily/LLM/main/local-ai-server/docker-compose.rtx5080-dual.yml

# Start dual models
docker compose -f docker-compose.rtx5080-dual.yml up -d

# Monitor both models
docker logs -f vllm-text
docker logs -f vllm-vision
```

**First startup: ~15-20 minutes** (downloads two 7B models ~7GB each)

---

## Model Recommendations for 16GB

### Best Quality (Single Model):

**1. Qwen2.5-14B-Instruct** (Recommended) ✅
- Best overall model for 16GB
- Excellent reasoning and coding
- Good multilingual support
- 16K context window

**2. Qwen2.5-Coder-14B-Instruct**
- Specialized for coding
- Same memory footprint
- Best for programming tasks

**3. Llama-3.1-8B-Instruct**
- Very efficient
- Meta's latest
- Great general purpose

---

### Dual Model Options:

**Text + Vision:**
- Qwen2.5-7B-Instruct + Qwen2.5-VL-7B-Instruct ✅

**Text + Code:**
- Qwen2.5-7B-Instruct + Qwen2.5-Coder-7B-Instruct

**General + Specialized:**
- Llama-3.1-8B + Mistral-7B-Instruct

---

## Performance Comparison

### RTX 5080 vs RTX 5090:

| Metric | RTX 5090 (32GB) | RTX 5080 (16GB) |
|--------|-----------------|-----------------|
| **Model Size** | 32B | 14B |
| **Quality** | Highest | Excellent |
| **Speed** | Fast | Very Fast |
| **Context** | 32K | 16K |
| **Dual Models** | 32B + 32B | 7B + 7B |

**Real-world impact:**
- 14B models are still very capable
- 7B models handle most tasks well
- Speed is actually faster (smaller model)
- Quality difference is noticeable but acceptable

---

## Monitoring VRAM Usage

### Check Current Usage:

```bash
# Watch GPU memory
watch -n 1 nvidia-smi

# Expected with 14B model:
# GPU Memory: ~13GB / 16GB (81%)

# Expected with dual 7B models:
# GPU Memory: ~14GB / 16GB (88%)
```

### If You See OOM (Out of Memory) Errors:

**Reduce memory utilization:**

```yaml
# In docker-compose file, reduce from 0.85 to 0.70
vllm:
  command:
    - --gpu-memory-utilization=0.70
```

**Or reduce context window:**

```yaml
# Reduce from 16384 to 8192
- --max-model-len=8192
```

---

## Quantization Option (Advanced)

### If You Want 32B Models on 16GB:

**Use AWQ quantization** (4-bit):

```yaml
vllm:
  command:
    - --model
    - TheBloke/Qwen2.5-32B-Instruct-AWQ
    # Quantized version fits in 16GB!
    - --quantization=awq
    - --gpu-memory-utilization=0.85
```

**Trade-offs:**
- ✅ Bigger model fits in 16GB
- ⚠️ Slight quality loss (usually minimal)
- ✅ Still better than 14B in many cases

**AWQ models available:**
- TheBloke/Qwen2.5-32B-Instruct-AWQ
- TheBloke/Llama-3.1-70B-Instruct-AWQ (tight fit)
- Many models on HuggingFace with -AWQ suffix

---

## Upgrade Path to RTX 5090

**When you get the RTX 5090:**

```bash
# 1. Stop current setup
docker compose -f docker-compose.rtx5080-16gb.yml down

# 2. Swap GPU physically

# 3. Use RTX 5090 config
docker compose -f docker-compose.enhanced-dual.yml up -d
# This uses 32B models!

# 4. Models download automatically
# All your data preserved
```

**No data loss, seamless upgrade!**

---

## Troubleshooting

### Issue: Model won't load - OOM error

**Solution 1: Reduce memory utilization**
```yaml
--gpu-memory-utilization=0.70  # From 0.85
```

**Solution 2: Use smaller model**
```yaml
--model=Qwen/Qwen2.5-7B-Instruct  # From 14B
```

**Solution 3: Reduce context**
```yaml
--max-model-len=8192  # From 16384
```

---

### Issue: Slow inference

**Check GPU utilization:**
```bash
nvidia-smi dmon -s um
# Should show high GPU usage (>80%)
```

**If low GPU usage:**
- Context may be too large
- Reduce `--max-model-len`
- Check for CPU bottleneck

---

### Issue: Want better quality

**Options:**
1. Use AWQ quantized 32B model
2. Wait for RTX 5090
3. Use dual 14B setup (not recommended - tight fit)

---

## Comparison Table

### Configuration Options:

| Setup | VRAM | Quality | Speed | Vision | Recommend |
|-------|------|---------|-------|--------|-----------|
| Single 14B | 13GB | ⭐⭐⭐⭐ | ⚡⚡⚡ | ❌ | ✅ Best |
| Dual 7B | 14GB | ⭐⭐⭐ | ⚡⚡⚡⚡ | ✅ | ✅ If need vision |
| Single 7B | 7GB | ⭐⭐⭐ | ⚡⚡⚡⚡⚡ | ❌ | ⚠️ For speed |
| 32B AWQ | 15GB | ⭐⭐⭐⭐⭐ | ⚡⚡ | ❌ | ⚠️ Advanced |

---

## Summary

**"What do we need to change for RTX 5080 16GB?"**

### Changes Required:
1. ✅ Use smaller models (14B or 7B instead of 32B)
2. ✅ Adjust GPU memory utilization (0.85 or 0.42 for dual)
3. ✅ May need shorter context windows
4. ✅ Use provided RTX 5080 configs

### Recommended Setup:
```bash
# Single 14B model (best quality)
docker compose -f docker-compose.rtx5080-16gb.yml up -d

# OR dual 7B models (for vision)
docker compose -f docker-compose.rtx5080-dual.yml up -d
```

### What Still Works:
- ✅ All 4 interfaces (Open WebUI, AnythingLLM, JupyterLab, API)
- ✅ 100% private and air-gapped
- ✅ Same installation process
- ✅ Same commands and workflows
- ✅ Excellent quality (just smaller models)

**Your RTX 5080 16GB will work great - just use the appropriate configs!** 🚀
