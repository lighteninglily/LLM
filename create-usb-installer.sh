#!/bin/bash
#
# Create USB Deployment Package
# This script creates a portable installer that can be copied to USB
# and run on the target Ubuntu machine without internet
#
# Usage:
#   ./create-usb-installer.sh /path/to/usb
#   Example: ./create-usb-installer.sh /mnt/usb
#

set -e

DEST_DIR=$1

if [ -z "$DEST_DIR" ]; then
    echo "Usage: ./create-usb-installer.sh /path/to/usb"
    echo "Example: ./create-usb-installer.sh /mnt/usb"
    exit 1
fi

if [ ! -d "$DEST_DIR" ]; then
    echo "Error: Directory $DEST_DIR does not exist"
    exit 1
fi

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo "================================================================"
echo "  Creating USB Deployment Package"
echo "================================================================"
echo ""
echo "Destination: $DEST_DIR"
echo ""

# Create deployment directory
USB_DIR="$DEST_DIR/llm-installer"
log_info "Creating directory: $USB_DIR"
mkdir -p "$USB_DIR"

# Copy all necessary files
log_info "Copying deployment files..."

# Scripts
cp install-ubuntu-rtx5090.sh "$USB_DIR/"
cp one-click-install.sh "$USB_DIR/"
cp start-dual-model.sh "$USB_DIR/"
cp stop-dual-model.sh "$USB_DIR/"
cp check-vram-usage.sh "$USB_DIR/"
cp deploy-web-facing.sh "$USB_DIR/"
cp bootstrap.sh "$USB_DIR/"
cp deploy.py "$USB_DIR/"
cp models.py "$USB_DIR/"
cp test_server.py "$USB_DIR/"
cp example-data-analysis.py "$USB_DIR/"
cp ai-data-analyst.py "$USB_DIR/"

# Configuration files
cp docker-compose.yml "$USB_DIR/"
cp docker-compose.enhanced.yml "$USB_DIR/"
cp docker-compose.enhanced-dual.yml "$USB_DIR/"
cp docker-compose.single-gpu.yml "$USB_DIR/"
cp docker-compose.ollama.yml "$USB_DIR/"
cp .env.example "$USB_DIR/"

# Documentation
cp README.md "$USB_DIR/"
cp QUICKSTART-UBUNTU.md "$USB_DIR/"
cp DEPLOYMENT-GUIDE-RTX5090.md "$USB_DIR/"
cp WEB-DEPLOYMENT-GUIDE.md "$USB_DIR/"
cp PRE-DEPLOYMENT-CHECKLIST.md "$USB_DIR/"
cp USB-INSTALL-GUIDE.md "$USB_DIR/" 2>/dev/null || true
cp ALTERNATIVES-COMPARISON.md "$USB_DIR/"
cp ENHANCEMENTS-SUMMARY.md "$USB_DIR/"
cp DUAL-MODEL-SETUP.md "$USB_DIR/"
cp HOW-RAG-WORKS.md "$USB_DIR/" 2>/dev/null || true
cp MODEL-CUSTOMIZATION-GUIDE.md "$USB_DIR/" 2>/dev/null || true
cp EMAIL-MARKETING-OPTIMIZER.md "$USB_DIR/" 2>/dev/null || true
cp PRODUCTION-DEPLOYMENT.md "$USB_DIR/" 2>/dev/null || true

# Make scripts executable
chmod +x "$USB_DIR"/*.sh
chmod +x "$USB_DIR"/*.py

# Create a simple README for the USB
cat > "$USB_DIR/START-HERE.txt" << 'EOF'
================================================================
  LLM Server USB Installer - Lightning Lily
================================================================

QUICK START OPTIONS:

Option 1 - ONE-CLICK INSTALL (RECOMMENDED):
1. Copy this entire 'llm-installer' folder to your Ubuntu machine
2. Open terminal and navigate to the folder
3. Run: chmod +x one-click-install.sh
4. Run: ./one-click-install.sh
5. Wait 60-90 minutes for installation
6. Access all 4 interfaces (see below)

Option 2 - STEP-BY-STEP INSTALL:
1. Copy folder to Ubuntu machine
2. Run: chmod +x install-ubuntu-rtx5090.sh
3. Run: ./install-ubuntu-rtx5090.sh
4. Follow on-screen instructions

WHAT'S INCLUDED:
- Automated Ubuntu 24.04 setup script
- NVIDIA RTX 5090 driver installation
- Docker + NVIDIA Container Toolkit
- vLLM inference engine (Qwen3-32B)
- 4 powerful interfaces:
  * Open WebUI (:3000) - ChatGPT-like interface
  * AnythingLLM (:3001) - Document RAG
  * JupyterLab (:8888) - Code execution
  * vLLM API (:8000) - Direct API access
- AI Data Analyst with code execution
- Email marketing optimization tools
- Complete documentation

REQUIREMENTS:
- Ubuntu 24.04 LTS
- NVIDIA RTX 5090 (or similar GPU)
- 64GB RAM recommended
- Internet connection (for model download)
- 100GB free disk space

DOCUMENTATION:
- READ ME FIRST: README.md
- Quick start: QUICKSTART-UBUNTU.md
- Detailed guide: DEPLOYMENT-GUIDE-RTX5090.md
- Enhancements: ENHANCEMENTS-SUMMARY.md
- Alternatives: ALTERNATIVES-COMPARISON.md

AFTER INSTALLATION ACCESS:
- http://localhost:3000 (Open WebUI - best for chat)
- http://localhost:3001 (AnythingLLM - best for RAG)
- http://localhost:8888 (JupyterLab - token: lightninglily)
- http://localhost:8000 (vLLM API - for programmatic access)

NEED HELP?
See README.md for full documentation and troubleshooting.

GitHub: https://github.com/lightninglily/LLM
================================================================
EOF

# Download offline installers (optional, commented out by default)
log_warn "Note: Large offline installers not included by default"
log_warn "Model will be downloaded during installation (requires internet)"

# Create checksums for verification
log_info "Creating checksums..."
cd "$USB_DIR"
sha256sum *.sh *.py *.yml *.md > CHECKSUMS.txt 2>/dev/null || true
cd - > /dev/null

# Create version file
cat > "$USB_DIR/VERSION.txt" << EOF
LLM Server Installer
Version: 1.0.0
Build Date: $(date +%Y-%m-%d)
Target: Ubuntu 24.04 + RTX 5090
Model: Qwen3-32B-Instruct
Repository: https://github.com/lightninglily/LLM
EOF

# Summary
echo ""
echo "================================================================"
echo "  USB Package Created Successfully!"
echo "================================================================"
echo ""
echo "Location: $USB_DIR"
echo ""
echo "Files copied:"
ls -lh "$USB_DIR" | wc -l | xargs echo "  -"
echo ""
echo "Total size:"
du -sh "$USB_DIR"
echo ""
echo "Next steps:"
echo "  1. Safely eject USB drive"
echo "  2. Insert into Ubuntu machine"
echo "  3. Copy 'llm-installer' folder to home directory"
echo "  4. Follow instructions in START-HERE.txt"
echo ""
echo "Verification:"
echo "  - Check CHECKSUMS.txt for file integrity"
echo "  - See VERSION.txt for build information"
echo ""
