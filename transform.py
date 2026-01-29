#!/usr/bin/env python3
"""
RAGFlow Automation Toolkit - Step 2: Transform
Transforms relational/tabular data into narrative text using LLM.
Includes file splitting for KG optimization.
"""

import argparse
import csv
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests
import yaml
from tqdm import tqdm

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from entity_normalizer import normalize_record
    HAS_NORMALIZER = True
except ImportError:
    HAS_NORMALIZER = False
    normalize_record = lambda x: x  # passthrough if not available

# Setup logging
def setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"transform_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def load_settings(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_analysis(analysis_path: Path) -> dict:
    with open(analysis_path) as f:
        return json.load(f)


def load_prompt_template(prompts_dir: Path) -> str:
    prompt_file = prompts_dir / "transform.txt"
    with open(prompt_file) as f:
        return f.read()


def load_file_analysis_prompt(prompts_dir: Path) -> str:
    """Load the per-file analysis prompt template."""
    prompt_file = prompts_dir / "analyze_file.txt"
    with open(prompt_file) as f:
        return f.read()


def load_lookup_tables(input_dir: Path, lookup_configs: list, logger: logging.Logger) -> dict:
    """Load lookup tables into memory for ID resolution."""
    lookups = {}
    
    for config in lookup_configs:
        file_path = input_dir / config["file"]
        if not file_path.exists():
            logger.warning(f"Lookup file not found: {file_path}")
            continue
        
        key_col = config["key_column"]
        value_col = config["value_column"]
        table_name = config["file"].replace(".csv", "").replace(".json", "")
        
        logger.info(f"Loading lookup table: {config['file']} ({key_col} -> {value_col})")
        
        lookup_dict = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix == ".csv":
                    reader = csv.DictReader(f)
                    for row in reader:
                        if key_col in row and value_col in row:
                            lookup_dict[str(row[key_col])] = row[value_col]
                elif file_path.suffix == ".json":
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if key_col in item and value_col in item:
                                lookup_dict[str(item[key_col])] = item[value_col]
            
            lookups[table_name] = lookup_dict
            logger.info(f"  Loaded {len(lookup_dict)} entries")
        except Exception as e:
            logger.error(f"Failed to load lookup {config['file']}: {e}")
    
    return lookups


def format_lookups_for_prompt(lookups: dict) -> str:
    """Format lookup tables for inclusion in the transform prompt."""
    if not lookups:
        return "No lookup tables provided."
    
    parts = []
    for table_name, mapping in lookups.items():
        # Show first 20 mappings as examples
        examples = list(mapping.items())[:20]
        examples_str = ", ".join([f"{k}={v}" for k, v in examples])
        if len(mapping) > 20:
            examples_str += f" ... ({len(mapping)} total)"
        parts.append(f"{table_name}: {examples_str}")
    
    return "\n".join(parts)


def read_records_from_file(file_path: Path, logger: logging.Logger) -> list:
    """Read records from CSV, Excel, JSON, or text file."""
    records = []
    
    try:
        suffix = file_path.suffix.lower()
        
        if suffix == ".csv":
            if HAS_PANDAS:
                df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
                records = df.to_dict('records')
            else:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        records.append(dict(row))
        
        elif suffix in [".xlsx", ".xls"]:
            if HAS_PANDAS:
                # Read all sheets
                xlsx = pd.ExcelFile(file_path)
                for sheet_name in xlsx.sheet_names:
                    df = pd.read_excel(xlsx, sheet_name=sheet_name, dtype=str, keep_default_na=False)
                    sheet_records = df.to_dict('records')
                    # Add sheet name as metadata if multiple sheets
                    if len(xlsx.sheet_names) > 1:
                        for rec in sheet_records:
                            rec['_sheet'] = sheet_name
                    records.extend(sheet_records)
                logger.info(f"  Read from {len(xlsx.sheet_names)} sheet(s)")
            else:
                logger.error(f"Cannot read Excel file without pandas: {file_path}")
        
        elif suffix == ".json":
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict):
                    for key in ["data", "records", "items", "results", "rows"]:
                        if key in data and isinstance(data[key], list):
                            records = data[key]
                            break
                    if not records:
                        records = [data]
        
        elif suffix == ".parquet":
            if HAS_PANDAS:
                df = pd.read_parquet(file_path)
                records = df.to_dict('records')
            else:
                logger.error(f"Cannot read Parquet file without pandas: {file_path}")
        
        else:
            # For text files, treat each line as a record
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append({"content": line})
        
        logger.info(f"Read {len(records)} records from {file_path.name}")
        
        # Normalize entity names for KG consistency
        if HAS_NORMALIZER and records:
            records = [normalize_record(r) if isinstance(r, dict) else r for r in records]
            logger.info(f"  Normalized entity names for {len(records)} records")
            
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
    
    return records


def format_records_for_prompt(records: list) -> str:
    """Format a batch of records for the LLM prompt."""
    parts = []
    for i, record in enumerate(records, 1):
        if isinstance(record, dict):
            fields = ", ".join([f"{k}: {v}" for k, v in record.items() if v])
            parts.append(f"{i}. {fields}")
        else:
            parts.append(f"{i}. {record}")
    return "\n".join(parts)


def call_llm_transform(prompt: str, settings: dict, logger: logging.Logger) -> str:
    """Call the LLM to transform records to narrative."""
    llm_config = settings["llm"]["transform"]
    endpoint = llm_config["endpoint"]
    model = llm_config["model"]
    
    url = f"{endpoint}/chat/completions"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 8192
    }
    
    try:
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        logger.error(f"LLM API error: {e}")
        raise


def analyze_file_schema(file_path: Path, records: list, settings: dict, 
                        logger: logging.Logger, prompts_dir: Path) -> dict:
    """Analyze a single file to get file-specific entity types and relationships."""
    if not records:
        return {}
    
    # Get schema from first record
    schema = list(records[0].keys()) if isinstance(records[0], dict) else []
    
    # Get sample records (first 5)
    sample_records = records[:5]
    sample_str = "\n".join([
        f"{i+1}. " + ", ".join([f"{k}: {v}" for k, v in rec.items() if v and not k.startswith('_')])
        for i, rec in enumerate(sample_records) if isinstance(rec, dict)
    ])
    
    # Load and format analysis prompt
    try:
        analysis_prompt_template = load_file_analysis_prompt(prompts_dir)
    except FileNotFoundError:
        logger.warning("Per-file analysis prompt not found, using default analysis")
        return {"record_type": "generic", "entities": [], "relationships": []}
    
    prompt = analysis_prompt_template.replace("{filename}", file_path.name)
    prompt = prompt.replace("{schema}", ", ".join(schema))
    prompt = prompt.replace("{sample_records}", sample_str)
    
    # Call LLM for analysis
    llm_config = settings["llm"]["analysis"]
    endpoint = llm_config["endpoint"]
    model = llm_config["model"]
    
    url = f"{endpoint}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Parse JSON from response
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            json_str = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            json_str = content[start:end].strip()
        else:
            json_str = content.strip()
        
        analysis = json.loads(json_str)
        logger.info(f"  File analysis: {analysis.get('record_type', 'unknown')} - {len(analysis.get('entities', []))} entities")
        return analysis
        
    except Exception as e:
        logger.warning(f"File analysis failed: {e}, using defaults")
        return {"record_type": "generic", "entities": [], "relationships": []}


def format_meta_tag_instructions(file_analysis: dict) -> str:
    """Generate META tag instructions from file analysis."""
    sensitive_fields = file_analysis.get("retrieval_sensitive_fields", [])
    if not sensitive_fields:
        return ""
    
    instructions = """
=== METADATA TAGS FOR RETRIEVAL (CRITICAL) ===
Each paragraph MUST start with a [META: ...] tag line containing key fields for exact-match search.
This is critical because semantic search cannot distinguish similar values (e.g., "December 3" vs "December 8").

TAG FORMAT: [META: key1=value1 | key2=value2 | key3=value3]

FIELDS TO INCLUDE IN TAGS:
"""
    for field in sensitive_fields:
        tag_key = field.get("tag_key", field.get("field", "unknown"))
        column = field.get("column", "unknown")
        fmt = field.get("format", "raw")
        reason = field.get("reason", "")
        
        if fmt == "YYYY-MM-DD":
            instructions += f"- {tag_key}: Extract from '{column}' column, format as YYYY-MM-DD (e.g., date=2025-12-03)\n"
        elif fmt == "UPPERCASE_UNDERSCORE":
            instructions += f"- {tag_key}: Extract from '{column}' column, format as UPPERCASE_WITH_UNDERSCORES (e.g., machine=CLIFFORD_MMW)\n"
        else:
            instructions += f"- {tag_key}: Extract from '{column}' column, use exact value (e.g., {tag_key}=VALUE)\n"
    
    instructions += """
EXAMPLE OUTPUT:
[META: date=2025-12-03 | machine=CLIFFORD_MMW | product=IMG4-44-2015 | order=254980]
CLIFFORD MMW produced 800 units of IMG4-44-2015 on December 3, 2025. Order 254980 achieved 124.25% yield rate.

RULES:
1. EVERY paragraph must have a [META: ...] tag as its FIRST line
2. Include ALL available tag fields from the record
3. Use exact values - no paraphrasing in tags
4. Tags enable keyword search; narrative enables semantic search
"""
    return instructions


def build_file_specific_prompt(base_prompt: str, file_analysis: dict, source_file: str) -> str:
    """Enhance the transform prompt with file-specific analysis."""
    if not file_analysis:
        return base_prompt
    
    # Build extra guidance sections
    extra_sections = []
    
    # Add record type and domain context
    record_type = file_analysis.get("record_type", "record")
    domain = file_analysis.get("domain", "business")
    extra_sections.append(f"""
FILE-SPECIFIC CONTEXT:
- Record Type: {record_type}
- Domain: {domain}
- Source: {source_file}""")
    
    # Add META tag instructions (CRITICAL for retrieval)
    meta_instructions = format_meta_tag_instructions(file_analysis)
    if meta_instructions:
        extra_sections.append(meta_instructions)
    
    # Add suggested relationship phrases
    phrases = file_analysis.get("suggested_phrases", file_analysis.get("suggested_relationship_phrases", []))
    if phrases:
        extra_sections.append("""
SUGGESTED RELATIONSHIP PHRASES FOR THIS FILE:
""" + "\n".join([f"- {p}" for p in phrases[:5]]))
    
    # Add canonical mappings if present
    mappings = file_analysis.get("canonical_mappings", {})
    if mappings:
        mapping_lines = [f"  {k} → {v}" for k, v in list(mappings.items())[:10]]
        extra_sections.append("""
CANONICAL NAME MAPPINGS (use the canonical form):
""" + "\n".join(mapping_lines))
    
    # Combine all extra guidance
    extra_guidance = "\n".join(extra_sections)
    
    # Insert after SOURCE CONTEXT section
    if "LOOKUP VALUES" in base_prompt:
        base_prompt = base_prompt.replace(
            "LOOKUP VALUES",
            extra_guidance + "\n\nLOOKUP VALUES"
        )
    
    return base_prompt


def transform_batch(records: list, lookups: dict, prompt_template: str, 
                   settings: dict, logger: logging.Logger,
                   source_file: str = "", sheet_name: str = "", schema_desc: str = "") -> str:
    """Transform a batch of records using the LLM."""
    lookups_str = format_lookups_for_prompt(lookups)
    records_str = format_records_for_prompt(records)
    
    prompt = prompt_template.replace("{lookups}", lookups_str).replace("{records}", records_str)
    # Add source context if using v2 prompt
    prompt = prompt.replace("{source_file}", source_file)
    prompt = prompt.replace("{sheet_name}", sheet_name or "Main")
    prompt = prompt.replace("{schema_description}", schema_desc)
    
    return call_llm_transform(prompt, settings, logger)


def transform_file(file_path: Path, output_dir: Path, lookups: dict,
                  prompt_template: str, settings: dict, logger: logging.Logger,
                  prompts_dir: Path = None) -> list:
    """Transform a single file, splitting output if needed."""
    records = read_records_from_file(file_path, logger)
    if not records:
        return []
    
    batch_size = settings["llm"]["transform"]["batch_size"]
    max_records_per_file = settings["kg"]["max_records_per_file"]
    
    # Extract source context for v2 prompt
    source_file = file_path.name
    sheet_name = ""
    if "_" in source_file and ".xlsm_" in source_file:
        parts = source_file.split(".xlsm_")
        sheet_name = parts[1].replace(".csv", "") if len(parts) > 1 else ""
    
    # Build schema description from first record
    schema_desc = ""
    if records and isinstance(records[0], dict):
        schema_desc = ", ".join(records[0].keys())
    
    # ===== NEW: Per-file analysis for file-specific prompts =====
    file_analysis = {}
    if prompts_dir:
        logger.info(f"  Analyzing file schema...")
        file_analysis = analyze_file_schema(file_path, records, settings, logger, prompts_dir)
    
    # Build file-specific prompt with analysis results
    file_prompt = build_file_specific_prompt(prompt_template, file_analysis, source_file)
    
    # Process records in batches
    all_paragraphs = []
    num_batches = (len(records) + batch_size - 1) // batch_size
    
    logger.info(f"Transforming {file_path.name}: {len(records)} records in {num_batches} batches")
    
    for i in tqdm(range(0, len(records), batch_size), desc=f"  {file_path.name}", leave=False):
        batch = records[i:i+batch_size]
        try:
            result = transform_batch(batch, lookups, file_prompt, settings, logger,
                                    source_file=source_file, sheet_name=sheet_name, 
                                    schema_desc=schema_desc)
            # Split result into paragraphs
            paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
            all_paragraphs.extend(paragraphs)
        except Exception as e:
            logger.error(f"Batch {i//batch_size + 1} failed: {e}")
            continue
    
    # Split into multiple output files if needed
    output_files = []
    base_name = file_path.stem
    
    if len(all_paragraphs) <= max_records_per_file:
        # Single output file
        output_file = output_dir / f"{base_name}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(all_paragraphs))
        output_files.append(output_file)
        logger.info(f"  Wrote {len(all_paragraphs)} paragraphs to {output_file.name}")
    else:
        # Split into multiple files
        num_files = (len(all_paragraphs) + max_records_per_file - 1) // max_records_per_file
        logger.info(f"  Splitting into {num_files} files (max {max_records_per_file} records each)")
        
        for file_num in range(num_files):
            start = file_num * max_records_per_file
            end = min(start + max_records_per_file, len(all_paragraphs))
            chunk = all_paragraphs[start:end]
            
            output_file = output_dir / f"{base_name}_{file_num+1:03d}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("\n\n".join(chunk))
            output_files.append(output_file)
            logger.info(f"  Wrote {len(chunk)} paragraphs to {output_file.name}")
    
    return output_files


def copy_file(src: Path, dst_dir: Path, logger: logging.Logger) -> Path:
    """Copy a file that doesn't need transformation."""
    dst = dst_dir / src.name
    with open(src, 'r', encoding='utf-8', errors='replace') as f_in:
        content = f_in.read()
    with open(dst, 'w', encoding='utf-8') as f_out:
        f_out.write(content)
    logger.info(f"Copied: {src.name}")
    return dst


def transform(input_dir: Path, output_dir: Path, analysis: dict, 
              settings: dict, logger: logging.Logger) -> dict:
    """Main transformation function."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load lookup tables
    lookups = load_lookup_tables(input_dir, analysis.get("lookup_tables", []), logger)
    
    # Load prompt template
    script_dir = Path(__file__).parent
    prompt_template = load_prompt_template(script_dir / "prompts")
    
    # Get list of lookup file names to exclude
    lookup_files = {cfg["file"] for cfg in analysis.get("lookup_tables", [])}
    
    results = {
        "transformed": [],
        "copied": [],
        "skipped": [],
        "errors": []
    }
    
    # Process each file based on analysis
    for file_config in analysis.get("files", []):
        file_name = file_config["name"]
        file_path = input_dir / file_name
        
        if not file_path.exists():
            logger.warning(f"File not found: {file_name}")
            results["skipped"].append(file_name)
            continue
        
        # Skip lookup tables
        if file_name in lookup_files:
            if settings["processing"]["exclude_lookup_from_kg"]:
                logger.info(f"Skipping lookup table: {file_name}")
                results["skipped"].append(file_name)
                continue
        
        if file_config.get("transform", False):
            # Transform this file with per-file analysis
            try:
                output_files = transform_file(file_path, output_dir, lookups, 
                                             prompt_template, settings, logger,
                                             prompts_dir=script_dir / "prompts")
                results["transformed"].extend([f.name for f in output_files])
            except Exception as e:
                logger.error(f"Failed to transform {file_name}: {e}")
                results["errors"].append({"file": file_name, "error": str(e)})
        else:
            # Copy as-is (already narrative)
            try:
                output_file = copy_file(file_path, output_dir, logger)
                results["copied"].append(output_file.name)
            except Exception as e:
                logger.error(f"Failed to copy {file_name}: {e}")
                results["errors"].append({"file": file_name, "error": str(e)})
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Transform data files to narrative text")
    parser.add_argument("--input", "-i", required=True, help="Input directory")
    parser.add_argument("--output", "-o", default="./output", help="Output directory")
    parser.add_argument("--config", "-c", default=None, help="Config file")
    parser.add_argument("--analysis", "-a", default=None, help="Analysis JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()
    config_file = Path(args.config) if args.config else script_dir / "config" / "settings.yaml"
    analysis_file = Path(args.analysis) if args.analysis else script_dir / "config" / "analysis_output.json"
    
    # Setup logging
    logger = setup_logging(script_dir / "logs")
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Validate inputs
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)
    
    if not analysis_file.exists():
        logger.error(f"Analysis file not found: {analysis_file}")
        logger.error("Run analyze.py first")
        sys.exit(1)
    
    # Load configs
    settings = load_settings(config_file)
    analysis = load_analysis(analysis_file)
    
    # Run transformation
    try:
        results = transform(input_dir, output_dir, analysis, settings, logger)
        
        # Print summary
        print("\n" + "="*60)
        print("TRANSFORMATION COMPLETE")
        print("="*60)
        print(f"Transformed: {len(results['transformed'])} files")
        print(f"Copied (no transform needed): {len(results['copied'])} files")
        print(f"Skipped (lookup tables): {len(results['skipped'])} files")
        print(f"Errors: {len(results['errors'])} files")
        print(f"\nOutput directory: {output_dir}")
        print("="*60)
        
        if results["errors"]:
            logger.warning("Some files had errors - check logs for details")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
