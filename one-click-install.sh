#!/bin/bash
#
# ONE-CLICK INSTALLER - Lightning Lily AI Server
# 
# This script does EVERYTHING:
# 1. Installs NVIDIA drivers
# 2. Installs Docker
# 3. Sets up the AI server with multiple interfaces
# 4. Starts all services
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/lighteninglily/LLM/main/one-click-install.sh | bash
#
# Or download and run:
#   chmod +x one-click-install.sh
#   ./one-click-install.sh
#

set -e

# =============================================================================
# Configuration
# =============================================================================
INSTALL_DIR="$HOME/.local-ai-server"
REPO_URL="https://raw.githubusercontent.com/lighteninglily/LLM/main"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# =============================================================================
# Helper Functions
# =============================================================================
print_header() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${BOLD}$1${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_error "Do not run as root! Run as normal user with sudo privileges."
        exit 1
    fi
}

check_ubuntu() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "ubuntu" ]]; then
            print_warning "This script is designed for Ubuntu. Detected: $ID $VERSION_ID"
            read -p "Continue anyway? [y/N] " -n 1 -r
            echo
            [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
        fi
    fi
}

check_gpu() {
    if ! lspci | grep -i nvidia > /dev/null; then
        print_error "No NVIDIA GPU detected!"
        exit 1
    fi
    print_success "NVIDIA GPU detected"
}

needs_reboot() {
    echo ""
    print_warning "REBOOT REQUIRED!"
    print_warning "Run this script again after reboot to continue installation."
    echo ""
    read -p "Reboot now? [Y/n] " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Nn]$ ]] && sudo reboot
    exit 0
}

# =============================================================================
# Installation Steps
# =============================================================================

install_nvidia_drivers() {
    print_header "NVIDIA Drivers"
    
    if command -v nvidia-smi &> /dev/null; then
        print_success "NVIDIA drivers already installed"
        nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
        return 0
    fi
    
    print_step "Installing NVIDIA drivers..."
    sudo apt-get update
    sudo apt-get install -y ubuntu-drivers-common
    sudo ubuntu-drivers install
    
    print_success "Drivers installed"
    needs_reboot
}

install_docker() {
    print_header "Docker"
    
    if command -v docker &> /dev/null; then
        print_success "Docker already installed"
        return 0
    fi
    
    print_step "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    
    print_success "Docker installed"
    print_warning "You may need to log out and back in for docker group to take effect"
}

install_nvidia_container_toolkit() {
    print_header "NVIDIA Container Toolkit"
    
    # Test if it works
    if docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi &> /dev/null; then
        print_success "NVIDIA Container Toolkit already working"
        return 0
    fi
    
    print_step "Installing NVIDIA Container Toolkit..."
    
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
        sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg 2>/dev/null || true
    
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null
    
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    
    # Test
    sleep 2
    if docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi &> /dev/null; then
        print_success "NVIDIA Container Toolkit working"
    else
        print_error "Container toolkit test failed. Try logging out and back in."
        exit 1
    fi
}

setup_directories() {
    print_header "Setting Up Directories"
    
    mkdir -p "$INSTALL_DIR"/{models,data/{anythingllm,open-webui,documents,notebooks,analysis}}
    
    print_success "Created directory structure at $INSTALL_DIR"
}

create_env_file() {
    print_header "Creating Configuration"
    
    if [ -f "$INSTALL_DIR/.env" ]; then
        print_success "Configuration already exists"
        return 0
    fi
    
    cat > "$INSTALL_DIR/.env" << 'EOF'
# =============================================================================
# Lightning Lily AI Server Configuration
# =============================================================================

# HuggingFace token (for gated models like Llama)
# Get yours at: https://huggingface.co/settings/tokens
HF_TOKEN=

# Model Configuration
LLM_MODEL=Qwen/Qwen3-32B-Instruct
LLM_MODEL_NAME=Qwen3-32B-Instruct
TENSOR_PARALLEL_SIZE=1
MAX_MODEL_LEN=8192
GPU_MEMORY_UTIL=0.85

# Server Ports
VLLM_PORT=8000
OPENWEBUI_PORT=3000
ANYTHINGLLM_PORT=3001
JUPYTER_PORT=8888

# Storage
MODELS_DIR=~/.local-ai-server/models
DATA_DIR=~/.local-ai-server/data

# Security
PASSWORDLESS_AUTH=false
WEBUI_AUTH=true
JUPYTER_TOKEN=lightninglily

# Optional API keys (for fallback/hybrid setups)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
EOF

    print_success "Created configuration at $INSTALL_DIR/.env"
    print_warning "Edit .env to add HuggingFace token for gated models"
}

download_compose_files() {
    print_header "Downloading Docker Compose Files"
    
    cd "$INSTALL_DIR"
    
    # Download enhanced compose file
    print_step "Downloading docker-compose configuration..."
    curl -fsSL "$REPO_URL/docker-compose.enhanced.yml" -o docker-compose.yml 2>/dev/null || {
        print_warning "Download failed, using fallback configuration..."
        cp "$INSTALL_DIR/../docker-compose.enhanced.yml" docker-compose.yml 2>/dev/null || {
            print_error "Could not find docker-compose configuration"
            exit 1
        }
    }
    
    print_success "Docker Compose configuration ready"
}

create_helper_scripts() {
    print_header "Creating Helper Scripts"
    
    # Start script
    cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash
cd ~/.local-ai-server
docker compose --env-file .env up -d
echo ""
echo "Services starting... (model download may take 10-20 minutes on first run)"
echo ""
echo "Access points:"
echo "  🌐 Open WebUI:   http://localhost:3000  (ChatGPT-like interface)"
echo "  📚 AnythingLLM:  http://localhost:3001  (Document RAG)"
echo "  📊 JupyterLab:   http://localhost:8888  (Code execution)"
echo "  🔌 vLLM API:     http://localhost:8000  (Direct API)"
echo ""
echo "Monitor startup: docker compose logs -f vllm"
EOF
    chmod +x "$INSTALL_DIR/start.sh"

    # Stop script
    cat > "$INSTALL_DIR/stop.sh" << 'EOF'
#!/bin/bash
cd ~/.local-ai-server
docker compose down
echo "All services stopped."
EOF
    chmod +x "$INSTALL_DIR/stop.sh"

    # Status script
    cat > "$INSTALL_DIR/status.sh" << 'EOF'
#!/bin/bash
echo "=== GPU Status ==="
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv
echo ""
echo "=== Container Status ==="
docker compose -f ~/.local-ai-server/docker-compose.yml ps
echo ""
echo "=== Service Health ==="
curl -s http://localhost:8000/health > /dev/null && echo "✓ vLLM: Running" || echo "✗ vLLM: Down"
curl -s http://localhost:3000/health > /dev/null && echo "✓ Open WebUI: Running" || echo "✗ Open WebUI: Down"
curl -s http://localhost:3001/api/ping > /dev/null && echo "✓ AnythingLLM: Running" || echo "✗ AnythingLLM: Down"
curl -s http://localhost:8888 > /dev/null && echo "✓ JupyterLab: Running" || echo "✗ JupyterLab: Down"
EOF
    chmod +x "$INSTALL_DIR/status.sh"

    # Logs script
    cat > "$INSTALL_DIR/logs.sh" << 'EOF'
#!/bin/bash
cd ~/.local-ai-server
docker compose logs -f "$@"
EOF
    chmod +x "$INSTALL_DIR/logs.sh"

    # Upload data shortcut
    cat > "$INSTALL_DIR/upload-data.sh" << 'EOF'
#!/bin/bash
# Quick way to copy files to the documents folder
if [ -z "$1" ]; then
    echo "Usage: ./upload-data.sh <file-or-folder>"
    echo "Files will be available in AnythingLLM and JupyterLab"
    exit 1
fi

cp -r "$@" ~/.local-ai-server/data/documents/
echo "✓ Copied to ~/.local-ai-server/data/documents/"
echo "  - Available in AnythingLLM for RAG"
echo "  - Available in JupyterLab at /home/jovyan/data/"
EOF
    chmod +x "$INSTALL_DIR/upload-data.sh"
    
    print_success "Created helper scripts"
}

pull_images() {
    print_header "Pulling Docker Images"
    print_warning "This may take 10-20 minutes depending on your internet speed..."
    
    cd "$INSTALL_DIR"
    docker compose pull
    
    print_success "All images downloaded"
}

start_services() {
    print_header "Starting Services"
    
    cd "$INSTALL_DIR"
    docker compose --env-file .env up -d
    
    print_success "Services starting..."
    print_warning "First startup downloads the model (~18GB) - this takes 10-20 minutes"
}

# =============================================================================
# Main Installation
# =============================================================================

main() {
    clear
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}                                                                ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}   ${BOLD}⚡ LIGHTNING LILY AI SERVER - ONE-CLICK INSTALLER ⚡${NC}         ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                                ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}   Local AI with:                                               ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}   • Qwen3-32B (State-of-the-Art 2026 Model)                   ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}   • Open WebUI (ChatGPT-like interface)                        ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}   • AnythingLLM (Document RAG)                                 ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}   • JupyterLab (Code execution)                                ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                                ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Pre-checks
    check_root
    check_ubuntu
    check_gpu
    
    echo ""
    read -p "Ready to install? [Y/n] " -n 1 -r
    echo
    [[ $REPLY =~ ^[Nn]$ ]] && exit 0
    
    # Installation steps
    sudo apt-get update
    sudo apt-get install -y curl wget git
    
    install_nvidia_drivers
    install_docker
    install_nvidia_container_toolkit
    setup_directories
    create_env_file
    download_compose_files
    create_helper_scripts
    pull_images
    start_services
    
    # Final message
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}                                                                ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}   ${BOLD}✓ INSTALLATION COMPLETE!${NC}                                    ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                                                                ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}Access your AI server:${NC}"
    echo ""
    echo -e "  ${CYAN}🌐 Open WebUI${NC}   → http://localhost:3000"
    echo -e "     Best for: General chat, similar to ChatGPT"
    echo ""
    echo -e "  ${CYAN}📚 AnythingLLM${NC}  → http://localhost:3001"
    echo -e "     Best for: Document upload, RAG, workspace management"
    echo ""
    echo -e "  ${CYAN}📊 JupyterLab${NC}   → http://localhost:8888"
    echo -e "     Token: lightninglily"
    echo -e "     Best for: Data analysis, code execution, visualizations"
    echo ""
    echo -e "  ${CYAN}🔌 vLLM API${NC}     → http://localhost:8000/v1"
    echo -e "     Best for: Programmatic access, integrations"
    echo ""
    echo -e "${BOLD}Quick commands:${NC}"
    echo "  ~/.local-ai-server/start.sh   - Start all services"
    echo "  ~/.local-ai-server/stop.sh    - Stop all services"
    echo "  ~/.local-ai-server/status.sh  - Check status"
    echo "  ~/.local-ai-server/logs.sh    - View logs"
    echo ""
    echo -e "${YELLOW}Note: First startup takes 10-20 minutes to download the model.${NC}"
    echo -e "${YELLOW}Monitor progress with: docker compose logs -f vllm${NC}"
    echo ""
}

main "$@"
