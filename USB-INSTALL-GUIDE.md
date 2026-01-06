# USB Installation Guide - Offline Deployment

## Overview

This guide explains how to create a USB deployment package and install the LLM server from USB drive on your Ubuntu machine.

**✨ Now includes ENHANCED STACK:**
- 🌐 Open WebUI (ChatGPT-like interface)
- 📚 AnythingLLM (Document RAG)
- 📊 JupyterLab (Code execution)
- 🔌 vLLM API (Direct access)
- 🚀 One-click installer option

---

## Why Use USB Installation?

- **Faster setup** - No need to download files during installation
- **Offline preparation** - Prepare on one machine, deploy on another
- **Multiple deployments** - Reuse USB for multiple servers
- **Backup** - Keep installation files as backup
- **Enhanced stack** - Get all 4 interfaces automatically

---

## Part 1: Creating USB Package (On Any Computer)

### Requirements
- USB drive (8GB minimum, 128GB recommended if including offline installers)
- This repository cloned locally

### Step 1: Format USB Drive

**Windows:**
```
1. Insert USB drive
2. Right-click → Format
3. File system: exFAT or FAT32
4. Quick Format
5. Start
```

**Linux:**
```bash
# Find USB device
lsblk

# Format (replace sdX with your USB device)
sudo mkfs.exfat /dev/sdX1

# Mount
sudo mount /dev/sdX1 /mnt/usb
```

### Step 2: Create Deployment Package

**On Linux:**
```bash
cd local-ai-server
chmod +x create-usb-installer.sh
./create-usb-installer.sh /mnt/usb
```

**On Windows:**
```bash
# Copy entire local-ai-server folder to USB
# Rename to: llm-installer
```

### Step 3: Verify Package

Check USB drive contains:
```
llm-installer/
├── START-HERE.txt
├── VERSION.txt
├── CHECKSUMS.txt
├── one-click-install.sh              ⭐ NEW: Automated installer
├── install-ubuntu-rtx5090.sh
├── deploy-web-facing.sh
├── deploy.py
├── models.py
├── ai-data-analyst.py                ⭐ NEW: Code execution
├── docker-compose.yml
├── docker-compose.enhanced.yml        ⭐ NEW: Enhanced stack
├── .env.example
├── ENHANCEMENTS-SUMMARY.md            ⭐ NEW: What's new guide
├── ALTERNATIVES-COMPARISON.md         ⭐ NEW: Solution comparison
└── All documentation files
```

### Step 4: Safely Eject USB

**Windows:** Right-click → Eject
**Linux:** `sudo umount /mnt/usb`

---

## Part 2: Installing from USB (On Ubuntu Machine)

### Requirements
- Fresh Ubuntu 24.04 LTS installation
- NVIDIA RTX 5090 GPU
- Internet connection (for model download)
- USB drive prepared from Part 1

### Step 1: Boot Ubuntu and Insert USB

1. Start Ubuntu machine
2. Insert USB drive
3. USB should auto-mount to `/media/username/USB_LABEL`

### Step 2: Copy Files to Home Directory

```bash
# Open terminal
cd ~

# Copy installer from USB
cp -r /media/$USER/*/llm-installer ~/

# Navigate to installer
cd ~/llm-installer

# Verify files
ls -la
cat VERSION.txt
```

### Step 3: Verify File Integrity (Optional)

```bash
# Check checksums
sha256sum -c CHECKSUMS.txt
```

All files should show "OK"

### Step 4: Run Installation

**⭐ NEW: Option 1 - One-Click Installer (RECOMMENDED)**

```bash
# Make script executable
chmod +x one-click-install.sh

# Run one-click installer
./one-click-install.sh
```

This installs EVERYTHING automatically including:
- ✅ NVIDIA drivers
- ✅ Docker + NVIDIA toolkit
- ✅ All 4 interfaces (vLLM, Open WebUI, AnythingLLM, JupyterLab)
- ✅ Helper scripts
- ✅ Starts all services

**Option 2 - Step-by-step Installer**

```bash
# Make script executable
chmod +x install-ubuntu-rtx5090.sh

# Run installer
./install-ubuntu-rtx5090.sh
```

**What happens:**
1. Updates Ubuntu packages (5 min)
2. Installs NVIDIA drivers (10 min)
3. **REBOOTS** (if drivers installed)
4. After reboot, run script again
5. Installs Docker (5 min)
6. Installs NVIDIA Container Toolkit (5 min)
7. Sets up AI server (5 min)
8. Downloads Qwen3-32B model (10-20 min)
9. Starts services

**Total time:** 60-90 minutes

### Step 5: Access Your AI Server

**All 4 interfaces available:**

```bash
# Open WebUI (ChatGPT-like)
firefox http://localhost:3000

# AnythingLLM (RAG)
firefox http://localhost:3001

# JupyterLab (Code execution)
firefox http://localhost:8888
# Token: lightninglily

# vLLM API (Programmatic)
curl http://localhost:8000/v1/models
```

**Best for:**
- Quick chat → Open WebUI (:3000)
- Document upload → AnythingLLM (:3001)
- Data analysis → JupyterLab (:8888)
- API integration → vLLM API (:8000)

Create admin accounts and start using!

---

## Part 3: Optional Web Deployment (From USB)

If you want web-facing access:

```bash
cd ~/llm-installer

# Make web script executable
chmod +x deploy-web-facing.sh

# Run with your domain
sudo ./deploy-web-facing.sh ai.yourdomain.com your@email.com
```

---

## Troubleshooting USB Installation

### USB Not Mounting

**Linux:**
```bash
# Find USB device
lsblk

# Mount manually
sudo mkdir -p /mnt/usb
sudo mount /dev/sdX1 /mnt/usb

# Copy files
cp -r /mnt/usb/llm-installer ~/
```

### Permission Denied on Scripts

```bash
# Fix all scripts at once
cd ~/llm-installer
chmod +x *.sh *.py
```

### Files Corrupted or Missing

```bash
# Verify checksums
sha256sum -c CHECKSUMS.txt

# If failed, copy from USB again
rm -rf ~/llm-installer
cp -r /media/$USER/*/llm-installer ~/
```

### Internet Connection Required

The installer needs internet to:
- Download Docker images (~2GB)
- Download Qwen3-32B model (~18GB)
- Install system packages

**Cannot install completely offline** without pre-downloading these.

---

## Advanced: Fully Offline Installation

To install without any internet connection, you need to pre-download:

### 1. Docker Images

**On machine with internet:**
```bash
# Pull images
docker pull vllm/vllm-openai:latest
docker pull mintplexlabs/anythingllm:latest

# Save to files
docker save vllm/vllm-openai:latest | gzip > vllm-image.tar.gz
docker save mintplexlabs/anythingllm:latest | gzip > anythingllm-image.tar.gz

# Copy to USB
cp *.tar.gz /mnt/usb/llm-installer/
```

**On target machine:**
```bash
cd ~/llm-installer

# Load images
docker load < vllm-image.tar.gz
docker load < anythingllm-image.tar.gz
```

### 2. Model Files

**Warning:** Model is ~18GB

**On machine with internet:**
```bash
# Install huggingface CLI
pip install huggingface-hub

# Download model
huggingface-cli download Qwen/Qwen3-32B-Instruct --local-dir ./qwen3-32b

# Copy to USB (requires ~20GB free space)
cp -r qwen3-32b /mnt/usb/llm-installer/
```

**On target machine:**
```bash
# Copy model to cache location
mkdir -p ~/.local-ai-server/models
cp -r ~/llm-installer/qwen3-32b ~/.local-ai-server/models/
```

### 3. Ubuntu Packages

For completely offline Ubuntu setup, you'd need:
- NVIDIA driver .deb packages
- Docker .deb packages
- All dependencies

This is complex - recommend using internet for initial setup.

---

## USB Package Contents

### Essential Files (Always Include)
- `install-ubuntu-rtx5090.sh` - Main installer
- `deploy.py` - Deployment automation
- `models.py` - Model management
- `test_server.py` - Testing utilities
- `docker-compose.yml` - Container config
- `.env.example` - Configuration template
- All `.md` documentation files

### Optional Files (For Advanced Use)
- `deploy-web-facing.sh` - Web deployment
- Alternative docker-compose files
- `example-data-analysis.py` - API examples

### Generated Files (Created by Script)
- `START-HERE.txt` - Quick start instructions
- `VERSION.txt` - Build information
- `CHECKSUMS.txt` - File integrity verification

---

## Multiple Machine Deployment

To deploy on multiple machines:

### Method 1: Reuse Same USB
1. Create USB package once
2. Use same USB for each machine
3. Takes 60-90 min per machine

### Method 2: Clone USB
1. Create master USB
2. Clone to multiple USB drives
3. Deploy simultaneously on multiple machines

**Clone USB (Linux):**
```bash
# Source USB
dd if=/dev/sdX of=~/usb-image.img bs=4M status=progress

# Write to new USB
dd if=~/usb-image.img of=/dev/sdY bs=4M status=progress
```

---

## Best Practices

### Before Creating USB
1. Test installation locally first
2. Verify all files are present
3. Check documentation is up to date
4. Run checksum verification

### During USB Creation
1. Use reliable USB drive (name brand)
2. Verify files copied correctly
3. Test USB on another machine if possible
4. Keep USB labeled and organized

### After Installation
1. Keep USB as backup
2. Update USB when software updates
3. Document any custom changes
4. Store in safe location

---

## Updating USB Package

When code changes:

```bash
# Get latest code
cd local-ai-server
git pull

# Recreate USB package
./create-usb-installer.sh /mnt/usb

# USB now has latest version
```

---

## USB Storage Requirements

### Minimum (Current Setup)
- **8GB USB** - Just scripts and documentation
- Model downloads during installation (~18GB)
- Docker images download during installation (~2GB)

### Recommended (With Offline Files)
- **128GB USB** - Includes pre-downloaded model and images
- Faster deployment (no downloads)
- Can deploy completely offline

---

## Security Notes

### USB Contains
- ✓ Scripts (no secrets)
- ✓ Configuration templates (no secrets)
- ✓ Documentation (public)

### USB Does NOT Contain
- ✗ API keys or tokens
- ✗ Passwords
- ✗ SSL certificates
- ✗ User data

**Safe to share USB** - no sensitive information included.

---

## Quick Reference

### Create USB Package
```bash
./create-usb-installer.sh /mnt/usb
```

### Install from USB
```bash
cp -r /media/$USER/*/llm-installer ~/
cd ~/llm-installer
chmod +x install-ubuntu-rtx5090.sh
./install-ubuntu-rtx5090.sh
```

### Verify Installation
```bash
docker compose ps
nvidia-smi
curl http://localhost:3001
```

---

## Support

If issues during USB installation:
1. Check `PRE-DEPLOYMENT-CHECKLIST.md`
2. Verify checksums with `CHECKSUMS.txt`
3. Check Ubuntu version (must be 24.04)
4. Ensure GPU is detected: `lspci | grep -i nvidia`
5. Check logs in installation output

**Repository:** https://github.com/lightninglily/LLM
