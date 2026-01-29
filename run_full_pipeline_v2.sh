#!/bin/bash
# Full Pipeline V2: Transform all 41 files → Upload → Parse → Run KG

set -e
cd /home/ryan/Documents/VSMS/ragflow_automation
source .venv/bin/activate

DATASET_ID="202ece22fb5111f0adf9dac365dd66f0"
API_KEY="ragflow-6uMjbYJWA95gN9sINHsc0J4SwkF8_yf2jIv3Couoa50"
API_URL="http://localhost:9380"
OUTPUT_DIR="./v2_output_full"
CHUNK_SIZE=128

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=============================================="
log "  FULL PIPELINE V2 - Starting"
log "=============================================="

# STEP 1: Transform all batches (pass directories)
log ""
log "=== STEP 1: TRANSFORMING ALL FILES ==="

for batch in v2_batch1 v2_batch2 v2_batch3; do
    if [ -d "./$batch" ]; then
        log ""
        log "--- Processing $batch ---"
        python transform.py --input "./$batch" --output "$OUTPUT_DIR" --verbose
    fi
done

OUTPUT_COUNT=$(find "$OUTPUT_DIR" -name "*.txt" 2>/dev/null | wc -l)
log ""
log "Transform complete: $OUTPUT_COUNT output files"

# STEP 2: Clear and update dataset
log ""
log "=== STEP 2: PREPARING DATASET ==="

curl -s -X PUT "$API_URL/api/v1/datasets/$DATASET_ID" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"parser_config\": {\"chunk_token_num\": $CHUNK_SIZE}}" > /dev/null

EXISTING_DOCS=$(curl -s "$API_URL/api/v1/datasets/$DATASET_ID/documents?page=1&page_size=100" \
    -H "Authorization: Bearer $API_KEY" | \
    python3 -c "import sys,json; docs=json.load(sys.stdin).get('data',{}).get('docs',[]); print(' '.join([d['id'] for d in docs]))" 2>/dev/null || echo "")

if [ -n "$EXISTING_DOCS" ]; then
    for doc_id in $EXISTING_DOCS; do
        curl -s -X DELETE "$API_URL/api/v1/datasets/$DATASET_ID/documents" \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json" \
            -d "{\"ids\": [\"$doc_id\"]}" > /dev/null
    done
    log "Deleted existing documents"
fi

# STEP 3: Upload
log ""
log "=== STEP 3: UPLOADING FILES ==="

UPLOAD_COUNT=0
for file in "$OUTPUT_DIR"/*.txt; do
    if [ -f "$file" ]; then
        curl -s -X POST "$API_URL/api/v1/datasets/$DATASET_ID/documents" \
            -H "Authorization: Bearer $API_KEY" \
            -F "file=@$file" > /dev/null
        UPLOAD_COUNT=$((UPLOAD_COUNT + 1))
        if [ $((UPLOAD_COUNT % 10)) -eq 0 ]; then
            log "  Uploaded $UPLOAD_COUNT files..."
        fi
    fi
done
log "Upload complete: $UPLOAD_COUNT files"

# STEP 4: Parse
log ""
log "=== STEP 4: PARSING CHUNKS ==="
sleep 5

DOC_IDS=$(curl -s "$API_URL/api/v1/datasets/$DATASET_ID/documents?page=1&page_size=200" \
    -H "Authorization: Bearer $API_KEY" | \
    python3 -c "import sys,json; docs=json.load(sys.stdin).get('data',{}).get('docs',[]); print(' '.join([d['id'] for d in docs]))")

for doc_id in $DOC_IDS; do
    curl -s -X POST "$API_URL/api/v1/datasets/$DATASET_ID/chunks" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"document_ids\": [\"$doc_id\"]}" > /dev/null
done

log "Waiting for parsing..."
while true; do
    STATS=$(curl -s "$API_URL/api/v1/datasets/$DATASET_ID/documents?page=1&page_size=200" \
        -H "Authorization: Bearer $API_KEY" | \
        python3 -c "
import sys,json
data=json.load(sys.stdin).get('data',{})
docs=data.get('docs',[])
done=sum(1 for d in docs if d.get('chunk_count',0) > 0)
chunks=sum(d.get('chunk_count',0) for d in docs)
print(f'{done}/{len(docs)} docs, {chunks} chunks')
")
    log "  Parsing: $STATS"
    
    DONE=$(echo "$STATS" | cut -d'/' -f1)
    TOTAL=$(echo "$STATS" | cut -d'/' -f2 | cut -d' ' -f1)
    
    if [ "$DONE" = "$TOTAL" ] && [ "$TOTAL" != "0" ]; then
        break
    fi
    sleep 30
done

log ""
log "=============================================="
log "  PIPELINE COMPLETE!"
log "=============================================="
log ""
log "TO START KG: Go to http://localhost:3002"
log "Open 'ASW Sales Orders V2 (Improved)' → Graph → Build"
