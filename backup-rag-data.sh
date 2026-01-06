#!/bin/bash
#
# Backup AnythingLLM RAG Data
# Backs up vector database, documents, and configuration
#
# Usage:
#   ./backup-rag-data.sh [backup-directory]
#   ./backup-rag-data.sh /mnt/backups
#

set -e

BACKUP_DIR=${1:-~/rag-backups}
DATA_DIR=~/.local-ai-server/data
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="rag-backup-$TIMESTAMP"

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
echo "  RAG Data Backup"
echo "================================================================"
echo ""

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    log_warn "Data directory not found: $DATA_DIR"
    log_warn "Is the AI server installed?"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

log_info "Creating backup: $BACKUP_NAME"
log_info "Destination: $BACKUP_PATH"
echo ""

# Stop containers for consistent backup
log_info "Stopping containers..."
cd ~/.local-ai-server
docker compose stop anythingllm

# Create backup
log_info "Backing up AnythingLLM data..."
tar -czf "$BACKUP_PATH.tar.gz" -C "$DATA_DIR" anythingllm

# Backup documents separately
if [ -d "$DATA_DIR/documents" ]; then
    log_info "Backing up documents..."
    tar -czf "$BACKUP_PATH-documents.tar.gz" -C "$DATA_DIR" documents
fi

# Backup configuration
log_info "Backing up configuration..."
cp ~/.local-ai-server/.env "$BACKUP_PATH.env" 2>/dev/null || true
cp ~/.local-ai-server/config.json "$BACKUP_PATH.config.json" 2>/dev/null || true

# Restart containers
log_info "Restarting containers..."
docker compose start anythingllm

# Create backup info file
cat > "$BACKUP_PATH.info" << EOF
Backup Information
==================
Date: $(date)
Hostname: $(hostname)
Data Size: $(du -sh "$DATA_DIR/anythingllm" | cut -f1)
Documents: $(find "$DATA_DIR/documents" -type f 2>/dev/null | wc -l) files
EOF

# Calculate sizes
BACKUP_SIZE=$(du -sh "$BACKUP_PATH.tar.gz" | cut -f1)

echo ""
echo "================================================================"
echo "  Backup Complete"
echo "================================================================"
echo ""
echo "Backup files:"
echo "  - Main data: $BACKUP_PATH.tar.gz ($BACKUP_SIZE)"
[ -f "$BACKUP_PATH-documents.tar.gz" ] && echo "  - Documents: $BACKUP_PATH-documents.tar.gz"
[ -f "$BACKUP_PATH.env" ] && echo "  - Config: $BACKUP_PATH.env"
echo ""
echo "To restore:"
echo "  ./restore-rag-data.sh $BACKUP_PATH.tar.gz"
echo ""
echo "Backup retention (keep last 7):"
ls -t "$BACKUP_DIR"/rag-backup-*.tar.gz | tail -n +8 | xargs rm -f 2>/dev/null || true
echo "  Cleaned old backups"
echo ""
