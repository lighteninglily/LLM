#!/bin/bash
#
# VRAM Usage Monitor for Dual-Model Setup
# Monitors GPU memory usage when running both Qwen3-32B and Qwen2.5-VL
#

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "================================================================"
echo "  GPU Memory Usage Monitor - Dual Model Setup"
echo "================================================================"
echo ""

# Check if nvidia-smi is available
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}Error: nvidia-smi not found${NC}"
    echo "This script requires NVIDIA GPU and drivers."
    exit 1
fi

# Function to format memory
format_memory() {
    local mem_mb=$1
    local mem_gb=$(echo "scale=2; $mem_mb / 1024" | bc)
    echo "${mem_gb}GB"
}

# Get GPU info
echo -e "${BLUE}GPU Information:${NC}"
nvidia-smi --query-gpu=name,driver_version,compute_cap --format=csv,noheader
echo ""

# Get memory info
echo -e "${BLUE}Memory Usage:${NC}"
mem_info=$(nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader,nounits)

mem_total=$(echo $mem_info | cut -d',' -f1 | xargs)
mem_used=$(echo $mem_info | cut -d',' -f2 | xargs)
mem_free=$(echo $mem_info | cut -d',' -f3 | xargs)

mem_percent=$(echo "scale=1; $mem_used * 100 / $mem_total" | bc)

echo "  Total:    $(format_memory $mem_total)"
echo "  Used:     $(format_memory $mem_used) (${mem_percent}%)"
echo "  Free:     $(format_memory $mem_free)"
echo ""

# Status indicator
if (( $(echo "$mem_percent < 80" | bc -l) )); then
    status_color=$GREEN
    status="HEALTHY"
elif (( $(echo "$mem_percent < 90" | bc -l) )); then
    status_color=$YELLOW
    status="WARNING - High Usage"
else
    status_color=$RED
    status="CRITICAL - Very High Usage"
fi

echo -e "Status: ${status_color}${status}${NC}"
echo ""

# Check if Docker containers are running
echo -e "${BLUE}Container Status:${NC}"

if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "vllm-text"; then
    echo -e "  vllm-text:   ${GREEN}RUNNING${NC}"
else
    echo -e "  vllm-text:   ${RED}STOPPED${NC}"
fi

if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "vllm-vision"; then
    echo -e "  vllm-vision: ${GREEN}RUNNING${NC}"
else
    echo -e "  vllm-vision: ${RED}STOPPED${NC}"
fi

echo ""

# Process details
echo -e "${BLUE}GPU Processes:${NC}"
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader | \
    awk -F',' '{printf "  PID: %-8s Process: %-30s Memory: %s\n", $1, $2, $3}'

echo ""

# Recommendations
if (( $(echo "$mem_percent > 85" | bc -l) )); then
    echo -e "${YELLOW}Recommendations:${NC}"
    echo "  - VRAM usage is high (>85%)"
    echo "  - Consider reducing --gpu-memory-utilization in docker-compose.enhanced-dual.yml"
    echo "  - Current setting: 0.38 for each model (76% total allocation)"
    echo "  - Try: 0.35 for each model (70% total allocation)"
    echo ""
fi

# Watch mode
if [ "$1" == "--watch" ]; then
    echo "Press Ctrl+C to exit watch mode"
    echo ""
    while true; do
        sleep 5
        clear
        $0
    done
fi

echo "================================================================"
echo "Tip: Run with --watch flag for continuous monitoring"
echo "     ./check-vram-usage.sh --watch"
echo "================================================================"
