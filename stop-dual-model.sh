#!/bin/bash
#
# Stop Dual-Model Setup
#

set -e

GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================"
echo "  Stopping Dual-Model Local AI Server"
echo "================================================================"
echo ""

docker compose -f docker-compose.enhanced-dual.yml down

echo ""
echo -e "${GREEN}All services stopped.${NC}"
echo ""
echo "To start again: ./start-dual-model.sh"
echo "================================================================"
