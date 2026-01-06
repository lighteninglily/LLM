#!/bin/bash
#
# Bootstrap script for Local AI Server
# Run this on a fresh Ubuntu 22.04/24.04 installation
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/lightninglily/LLM/main/bootstrap.sh | bash
#
# Or:
#   wget -qO- https://raw.githubusercontent.com/lightninglily/LLM/main/bootstrap.sh | bash
#

set -e

echo "========================================"
echo "  Local AI Server Bootstrap"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "Do not run this script as root!"
    log_error "Run as a normal user with sudo privileges."
    exit 1
fi

# Check Ubuntu version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        log_warn "This script is designed for Ubuntu. Your OS: $ID"
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

log_info "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

log_info "Installing base dependencies..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Check for NVIDIA GPU
log_info "Checking for NVIDIA GPU..."
if ! lspci | grep -i nvidia > /dev/null; then
    log_error "No NVIDIA GPU detected!"
    log_error "This system requires an NVIDIA GPU for LLM inference."
    exit 1
fi
log_info "NVIDIA GPU detected."

# Install NVIDIA drivers if not present
if ! command -v nvidia-smi &> /dev/null; then
    log_info "Installing NVIDIA drivers..."
    sudo apt-get install -y ubuntu-drivers-common
    sudo ubuntu-drivers autoinstall
    
    log_warn "NVIDIA drivers installed. A REBOOT IS REQUIRED!"
    log_warn "After reboot, run this script again to continue."
    
    read -p "Reboot now? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        sudo reboot
    fi
    exit 0
else
    log_info "NVIDIA drivers already installed."
    nvidia-smi --query-gpu=name,driver_version --format=csv
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    log_info "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    log_warn "Added $USER to docker group. You may need to log out and back in."
else
    log_info "Docker already installed."
fi

# Install NVIDIA Container Toolkit
if ! dpkg -l | grep -q nvidia-container-toolkit; then
    log_info "Installing NVIDIA Container Toolkit..."
    
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
        sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
else
    log_info "NVIDIA Container Toolkit already installed."
fi

# Test Docker GPU access
log_info "Testing Docker GPU access..."
if docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi > /dev/null 2>&1; then
    log_info "Docker can access GPU successfully!"
else
    log_error "Docker cannot access GPU."
    log_error "Try logging out and back in, or rebooting."
    exit 1
fi

# Clone or download the deployment tool
INSTALL_DIR="$HOME/local-ai-server"

if [ -d "$INSTALL_DIR" ]; then
    log_info "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull || true
else
    log_info "Downloading deployment tool..."
    
    # Try git clone first
    if git clone https://github.com/lightninglily/LLM.git "$INSTALL_DIR" 2>/dev/null; then
        log_info "Cloned repository."
    else
        # Fallback: create directory and download files directly
        mkdir -p "$INSTALL_DIR"
        cd "$INSTALL_DIR"
        
        log_warn "Git clone failed. Creating local installation..."
        
        # The files would be downloaded here in a real setup
        # For now, we'll just note that deploy.py should exist
        if [ ! -f "deploy.py" ]; then
            log_error "deploy.py not found. Please download it manually."
            exit 1
        fi
    fi
fi

cd "$INSTALL_DIR"

# Make scripts executable
chmod +x *.py 2>/dev/null || true
chmod +x *.sh 2>/dev/null || true

# Run hardware detection
log_info "Running hardware detection..."
python3 deploy.py detect

echo ""
echo "========================================"
echo "  Bootstrap Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Review the hardware report above"
echo ""
echo "2. Run the full installer:"
echo "   cd $INSTALL_DIR"
echo "   python3 deploy.py install"
echo ""
echo "3. Configure HuggingFace token (for gated models):"
echo "   Edit ~/.local-ai-server/.env"
echo "   Add: HF_TOKEN=your_token_here"
echo ""
echo "4. Start the server:"
echo "   ~/.local-ai-server/start.sh"
echo ""
echo "5. Access the UI:"
echo "   http://localhost:3001"
echo ""
