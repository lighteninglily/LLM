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
cp deploy-web-facing.sh "$USB_DIR/"
cp bootstrap.sh "$USB_DIR/"
cp deploy.py "$USB_DIR/"
cp models.py "$USB_DIR/"
cp test_server.py "$USB_DIR/"
cp example-data-analysis.py "$USB_DIR/"

# Configuration files
cp docker-compose.yml "$USB_DIR/"
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

# Make scripts executable
chmod +x "$USB_DIR"/*.sh
chmod +x "$USB_DIR"/*.py

# Create a simple README for the USB
cat > "$USB_DIR/START-HERE.txt" << 'EOF'
================================================================
  LLM Server USB Installer - Lightning Lily
================================================================

QUICK START:
1. Copy this entire 'llm-installer' folder to your Ubuntu machine
2. Open terminal and navigate to the folder
3. Run: chmod +x install-ubuntu-rtx5090.sh
4. Run: ./install-ubuntu-rtx5090.sh
5. Wait 60-90 minutes for installation
6. Access: http://localhost:3001

WHAT'S INCLUDED:
- Automated Ubuntu 24.04 setup script
- NVIDIA RTX 5090 driver installation
- Docker + NVIDIA Container Toolkit
- vLLM inference engine
- AnythingLLM web interface
- Qwen3-32B model (downloads automatically)
- Web deployment tools
- Complete documentation

REQUIREMENTS:
- Ubuntu 24.04 LTS
- NVIDIA RTX 5090 (or similar GPU)
- 64GB RAM recommended
- Internet connection (for model download)
- 100GB free disk space

DOCUMENTATION:
- READ ME FIRST: QUICKSTART-UBUNTU.md
- Detailed guide: DEPLOYMENT-GUIDE-RTX5090.md
- Web setup: WEB-DEPLOYMENT-GUIDE.md
- Issues checklist: PRE-DEPLOYMENT-CHECKLIST.md

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
