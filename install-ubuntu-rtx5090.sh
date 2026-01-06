#!/bin/bash
#
# Complete Ubuntu 24.04 Installation Script for RTX 5090 + Local AI Server
# This script handles everything from NVIDIA drivers to LLM deployment
#
# Usage:
#   chmod +x install-ubuntu-rtx5090.sh
#   ./install-ubuntu-rtx5090.sh
#

set -e

echo "================================================================"
echo "  Ubuntu 24.04 + RTX 5090 + Local AI Server Installation"
echo "================================================================"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "Do not run this script as root!"
    log_error "Run as a normal user with sudo privileges."
    exit 1
fi

# Check Ubuntu version
log_step "Checking Ubuntu Version"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        log_warn "This script is designed for Ubuntu 24.04. Your OS: $ID $VERSION_ID"
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    log_info "OS: $PRETTY_NAME"
fi

# Update system
log_step "Updating System Packages"
sudo apt-get update
sudo apt-get upgrade -y

# Install base dependencies
log_step "Installing Base Dependencies"
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
log_step "Checking for NVIDIA GPU"
if ! lspci | grep -i nvidia > /dev/null; then
    log_error "No NVIDIA GPU detected!"
    log_error "This system requires an NVIDIA GPU for LLM inference."
    exit 1
fi
log_info "NVIDIA GPU detected."

# Install NVIDIA drivers (550+ recommended for RTX 5090)
if ! command -v nvidia-smi &> /dev/null; then
    log_step "Installing NVIDIA Drivers (550+)"
    sudo apt-get install -y ubuntu-drivers-common
    
    # Install latest recommended driver
    sudo ubuntu-drivers install
    
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
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
fi

# Install Docker
if ! command -v docker &> /dev/null; then
    log_step "Installing Docker"
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    log_warn "Added $USER to docker group. You may need to log out and back in."
else
    log_info "Docker already installed."
    docker --version
fi

# Install NVIDIA Container Toolkit
if ! dpkg -l | grep -q nvidia-container-toolkit; then
    log_step "Installing NVIDIA Container Toolkit"
    
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
log_step "Testing Docker GPU Access"
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
    log_info "Installation directory already exists. Updating..."
    cd "$INSTALL_DIR"
    git pull || true
else
    log_step "Downloading Local AI Server Deployment Tool"
    
    # If you've already cloned the repo locally, use that
    if [ -d "$(pwd)/local-ai-server" ]; then
        cp -r "$(pwd)/local-ai-server" "$INSTALL_DIR"
        log_info "Copied from local directory."
    else
        # Otherwise create directory with files
        mkdir -p "$INSTALL_DIR"
        cd "$INSTALL_DIR"
        
        # Download the main files
        log_info "Downloading deploy.py..."
        wget https://raw.githubusercontent.com/lightninglily/LLM/main/deploy.py -O deploy.py || {
            log_error "Failed to download deploy.py. Check your internet connection."
            exit 1
        }
        wget https://raw.githubusercontent.com/lightninglily/LLM/main/models.py -O models.py
        wget https://raw.githubusercontent.com/lightninglily/LLM/main/test_server.py -O test_server.py
        
        chmod +x *.py
    fi
fi

cd "$INSTALL_DIR"

# Run hardware detection
log_step "Running Hardware Detection"
python3 deploy.py detect

# Run installer
log_step "Running Installation"
python3 deploy.py install

echo ""
echo "================================================================"
echo "  Installation Complete!"
echo "================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure HuggingFace token (for gated models like Llama):"
echo "   nano ~/.local-ai-server/.env"
echo "   Add: HF_TOKEN=your_token_here"
echo ""
echo "2. Start the server:"
echo "   ~/.local-ai-server/start.sh"
echo ""
echo "3. Access the UI:"
echo "   http://localhost:3001"
echo ""
echo "4. Recommended models for RTX 5090 (32GB VRAM):"
echo "   - Qwen/Qwen3-32B-Instruct (best quality)"
echo "   - google/gemma-3-27b (very fast)"
echo "   - Qwen/Qwen3-Coder-32B (coding)"
echo ""
echo "5. Monitor GPU usage:"
echo "   watch -n 1 nvidia-smi"
echo ""
