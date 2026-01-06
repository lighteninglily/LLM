#!/bin/bash
#
# Restore AnythingLLM RAG Data
# Restores vector database, documents, and configuration from backup
#
# Usage:
#   ./restore-rag-data.sh backup-file.tar.gz
#

set -e

BACKUP_FILE=$1
DATA_DIR=~/.local-ai-server/data

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore-rag-data.sh backup-file.tar.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo "================================================================"
echo "  RAG Data Restore"
echo "================================================================"
echo ""
echo "WARNING: This will overwrite existing RAG data!"
echo ""
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# Stop containers
log_info "Stopping containers..."
cd ~/.local-ai-server
docker compose stop anythingllm

# Backup existing data (just in case)
if [ -d "$DATA_DIR/anythingllm" ]; then
    log_warn "Backing up current data to $DATA_DIR/anythingllm.pre-restore..."
    mv "$DATA_DIR/anythingllm" "$DATA_DIR/anythingllm.pre-restore"
fi

# Restore
log_info "Restoring from: $BACKUP_FILE"
tar -xzf "$BACKUP_FILE" -C "$DATA_DIR"

# Restore documents if available
DOCS_BACKUP="${BACKUP_FILE%-*.tar.gz}-documents.tar.gz"
if [ -f "$DOCS_BACKUP" ]; then
    log_info "Restoring documents..."
    tar -xzf "$DOCS_BACKUP" -C "$DATA_DIR"
fi

# Restart containers
log_info "Restarting containers..."
docker compose start anythingllm

echo ""
echo "================================================================"
echo "  Restore Complete"
echo "================================================================"
echo ""
echo "Access your restored data at: http://localhost:3001"
echo ""
echo "If you need to rollback:"
echo "  mv $DATA_DIR/anythingllm.pre-restore $DATA_DIR/anythingllm"
echo "  docker compose restart anythingllm"
echo ""
