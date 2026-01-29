#!/bin/bash
# Run production files transform with intelligent META tagging
# Runs independently in background - safe to close terminal

cd /home/ryan/Documents/VSMS/ragflow_automation

# Activate virtual environment
source .venv/bin/activate

OUTPUT_DIR="./v3_output"
LOG_FILE="./logs/production_transform_$(date +%Y%m%d_%H%M%S).log"
STATUS_FILE="$OUTPUT_DIR/status.txt"

# Create output directory
mkdir -p "$OUTPUT_DIR"
mkdir -p ./logs

echo "Starting production files transform at $(date)" | tee "$LOG_FILE"
echo "Output: $OUTPUT_DIR" | tee -a "$LOG_FILE"
echo "Log: $LOG_FILE" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"

# Copy all production files to a single input directory for processing
TEMP_INPUT="./v3_input_production"
mkdir -p "$TEMP_INPUT"

echo "Copying production files..." | tee -a "$LOG_FILE"
cp ./v2_batch1/Daily\ Production\ Report\ v1.xlsm_*.csv "$TEMP_INPUT/" 2>/dev/null
cp ./v2_batch2/Daily\ Production\ Report\ v1.xlsm_*.csv "$TEMP_INPUT/" 2>/dev/null
cp ./v2_batch3/Daily\ Production\ Report\ v1.xlsm_*.csv "$TEMP_INPUT/" 2>/dev/null
cp ./v2_batch3/Production\ Sheet.xlsm_*.csv "$TEMP_INPUT/" 2>/dev/null

echo "Files to process: $(ls "$TEMP_INPUT"/*.csv 2>/dev/null | wc -l)" | tee -a "$LOG_FILE"
echo "RUNNING" > "$STATUS_FILE"

# Run transform
python3 transform.py \
    --input "$TEMP_INPUT" \
    --output "$OUTPUT_DIR" \
    --analysis ./config/production_files.json \
    2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?

# Update status
if [ $EXIT_CODE -eq 0 ]; then
    echo "COMPLETED at $(date)" > "$STATUS_FILE"
    echo "Output files: $(ls "$OUTPUT_DIR"/*.txt 2>/dev/null | wc -l)" >> "$STATUS_FILE"
else
    echo "FAILED with exit code $EXIT_CODE at $(date)" > "$STATUS_FILE"
fi

echo "----------------------------------------" | tee -a "$LOG_FILE"
echo "Transform finished at $(date) with exit code $EXIT_CODE" | tee -a "$LOG_FILE"
echo "Output files: $(ls "$OUTPUT_DIR"/*.txt 2>/dev/null | wc -l)" | tee -a "$LOG_FILE"

# Cleanup temp input
rm -rf "$TEMP_INPUT"
