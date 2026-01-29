#!/bin/bash
# Full pipeline: Transform all batches → Upload → Parse → Run KG
# Runs unattended

set -e
cd /home/ryan/Documents/VSMS/ragflow_automation
source .venv/bin/activate

DATASET_ID="202ece22fb5111f0adf9dac365dd66f0"
API_KEY="ragflow-6uMjbYJWA95gN9sINHsc0J4SwkF8_yf2jIv3Couoa50"
API_URL="http://localhost:9380"

LOG_FILE="pipeline_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Starting Full Pipeline at $(date) ==="

# Step 1: Transform all batches
echo ""
echo "=== STEP 1: Transforming all batches ==="

for batch in v2_batch1 v2_batch2 v2_batch3; do
    echo ""
    echo "--- Processing $batch ---"
    python transform.py --input ./$batch --output ./v2_output --verbose
done

echo ""
echo "=== Transform complete. Files in v2_output: ==="
ls -la ./v2_output/*.txt | wc -l
echo "files created"

# Step 2: Upload all transformed files
echo ""
echo "=== STEP 2: Uploading to RAGFlow ==="

for file in ./v2_output/*.txt; do
    filename=$(basename "$file")
    echo "Uploading: $filename"
    curl -s -X POST "$API_URL/api/v1/datasets/$DATASET_ID/documents" \
        -H "Authorization: Bearer $API_KEY" \
        -F "file=@$file" > /dev/null
done

echo "Upload complete"

# Step 3: Get document IDs and trigger parsing
echo ""
echo "=== STEP 3: Triggering chunk parsing ==="

sleep 5  # Wait for uploads to register

DOC_IDS=$(curl -s "$API_URL/api/v1/datasets/$DATASET_ID/documents?page=1&page_size=100" \
    -H "Authorization: Bearer $API_KEY" | \
    python3 -c "import sys,json; docs=json.load(sys.stdin).get('data',{}).get('docs',[]); print(' '.join([d['id'] for d in docs]))")

echo "Found $(echo $DOC_IDS | wc -w) documents"

# Parse in batches
for doc_id in $DOC_IDS; do
    curl -s -X POST "$API_URL/api/v1/datasets/$DATASET_ID/chunks" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"document_ids\": [\"$doc_id\"]}" > /dev/null
done

echo "Parsing triggered for all documents"

# Step 4: Wait for parsing to complete
echo ""
echo "=== STEP 4: Waiting for parsing to complete ==="

while true; do
    PROGRESS=$(curl -s "$API_URL/api/v1/datasets/$DATASET_ID/documents?page=1&page_size=100" \
        -H "Authorization: Bearer $API_KEY" | \
        python3 -c "
import sys,json
docs=json.load(sys.stdin).get('data',{}).get('docs',[])
total=len(docs)
done=sum(1 for d in docs if d.get('progress_msg','') in ['Done', ''] and d.get('chunk_count',0) > 0)
print(f'{done}/{total}')
")
    echo "Parsing progress: $PROGRESS documents complete"
    
    DONE=$(echo $PROGRESS | cut -d'/' -f1)
    TOTAL=$(echo $PROGRESS | cut -d'/' -f2)
    
    if [ "$DONE" = "$TOTAL" ] && [ "$TOTAL" != "0" ]; then
        echo "All documents parsed!"
        break
    fi
    
    sleep 30
done

# Step 5: Start Knowledge Graph generation
echo ""
echo "=== STEP 5: Starting Knowledge Graph generation ==="

curl -s -X POST "$API_URL/api/v1/datasets/$DATASET_ID/graphrag" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"entity_types": ["customer", "product", "order", "machine", "warehouse", "mine_site", "shipment", "production_run"]}'

echo "KG generation started!"

# Step 6: Monitor KG progress
echo ""
echo "=== STEP 6: Monitoring KG progress ==="

while true; do
    KG_STATUS=$(curl -s "$API_URL/api/v1/datasets/$DATASET_ID/trace_graphrag" \
        -H "Authorization: Bearer $API_KEY" | \
        python3 -c "
import sys,json
d=json.load(sys.stdin).get('data',{})
progress=d.get('progress',0)*100
duration=d.get('process_duration',0)/60
print(f'{progress:.1f}% complete, {duration:.1f} min elapsed')
")
    echo "KG: $KG_STATUS"
    
    if echo "$KG_STATUS" | grep -q "100.0%"; then
        echo ""
        echo "=== PIPELINE COMPLETE at $(date) ==="
        break
    fi
    
    sleep 60
done

echo ""
echo "=== All done! Check RAGFlow UI for results ==="
