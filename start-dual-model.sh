#!/bin/bash
#
# Start Dual-Model Setup
# Launches both Qwen3-32B (text) and Qwen2.5-VL (vision) models
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================"
echo "  Starting Dual-Model Local AI Server"
echo "================================================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}Created .env file${NC}"
        echo "Please edit .env and add your HF_TOKEN if needed."
        echo ""
    else
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
fi

# Check GPU
echo -e "${BLUE}Checking GPU...${NC}"
if ! nvidia-smi &> /dev/null; then
    echo -e "${RED}Error: nvidia-smi not found${NC}"
    echo "NVIDIA GPU and drivers are required."
    exit 1
fi

gpu_mem=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
gpu_mem_gb=$(echo "scale=0; $gpu_mem / 1024" | bc)

echo -e "${GREEN}✓${NC} GPU detected: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
echo "  Memory: ${gpu_mem_gb}GB"

if [ "$gpu_mem_gb" -lt 30 ]; then
    echo -e "${YELLOW}Warning: Less than 30GB VRAM detected${NC}"
    echo "Dual-model setup requires ~25-28GB VRAM"
    echo "You may experience OOM errors."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# Check if containers are already running
if docker ps | grep -q "vllm-text"; then
    echo -e "${YELLOW}Warning: Containers already running${NC}"
    read -p "Stop existing containers and restart? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping existing containers..."
        docker compose -f docker-compose.enhanced-dual.yml down
    else
        echo "Exiting..."
        exit 0
    fi
fi

# Start services
echo -e "${BLUE}Starting services...${NC}"
echo ""

docker compose -f docker-compose.enhanced-dual.yml up -d

echo ""
echo -e "${GREEN}Services started!${NC}"
echo ""

# Wait for health checks
echo -e "${BLUE}Waiting for models to load...${NC}"
echo "This may take 5-10 minutes on first run (downloading models)"
echo ""

# Monitor vllm-text startup
echo -n "  Text model (Qwen3-32B)...    "
for i in {1..120}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}READY${NC}"
        break
    fi
    sleep 5
    if [ $i -eq 120 ]; then
        echo -e "${RED}TIMEOUT${NC}"
        echo "Check logs: docker logs vllm-text"
    fi
done

# Monitor vllm-vision startup
echo -n "  Vision model (Qwen2.5-VL)... "
for i in {1..120}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}READY${NC}"
        break
    fi
    sleep 5
    if [ $i -eq 120 ]; then
        echo -e "${RED}TIMEOUT${NC}"
        echo "Check logs: docker logs vllm-vision"
    fi
done

# Check other services
echo -n "  Open WebUI...                "
sleep 5
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}READY${NC}"
else
    echo -e "${YELLOW}STARTING${NC}"
fi

echo -n "  AnythingLLM...               "
if curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo -e "${GREEN}READY${NC}"
else
    echo -e "${YELLOW}STARTING${NC}"
fi

echo -n "  JupyterLab...                "
if curl -s http://localhost:8888 > /dev/null 2>&1; then
    echo -e "${GREEN}READY${NC}"
else
    echo -e "${YELLOW}STARTING${NC}"
fi

echo ""
echo "================================================================"
echo -e "  ${GREEN}Dual-Model AI Server Ready!${NC}"
echo "================================================================"
echo ""
echo "Access URLs:"
echo "  Open WebUI:   http://localhost:3000   (Both models available!)"
echo "  AnythingLLM:  http://localhost:3001   (Text model for RAG)"
echo "  JupyterLab:   http://localhost:8888   (Token: lightninglily)"
echo ""
echo "API Endpoints:"
echo "  Text Model:   http://localhost:8000   (Qwen3-32B)"
echo "  Vision Model: http://localhost:8001   (Qwen2.5-VL)"
echo ""
echo "Model Selection:"
echo "  - Open WebUI: Click dropdown to switch between models"
echo "  - JupyterLab: Use different base_url for each model"
echo "  - AnythingLLM: Always uses text model (best for RAG)"
echo ""
echo "Monitoring:"
echo "  Check VRAM: ./check-vram-usage.sh"
echo "  Watch mode: ./check-vram-usage.sh --watch"
echo "  View logs:  docker compose -f docker-compose.enhanced-dual.yml logs -f"
echo ""
echo "Management:"
echo "  Stop:       ./stop-dual-model.sh"
echo "  Restart:    docker compose -f docker-compose.enhanced-dual.yml restart"
echo "================================================================"
