#!/usr/bin/env python3
"""
RAGFlow Automation Toolkit - Step 1: Analyze
Analyzes input data files to determine entity types and transformation needs.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
import yaml

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Setup logging
def setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"analyze_{timestamp}.log"
    
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
    """Load settings from YAML config file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_prompt_template(prompts_dir: Path) -> str:
    """Load the analysis prompt template."""
    prompt_file = prompts_dir / "analyze.txt"
    with open(prompt_file) as f:
        return f.read()


def detect_file_format(file_path: Path) -> str:
    """Detect file format based on extension and content."""
    ext = file_path.suffix.lower()
    if ext == ".csv":
        return "csv"
    elif ext == ".json":
        return "json"
    elif ext in [".txt", ".text"]:
        return "text"
    elif ext in [".md", ".markdown"]:
        return "markdown"
    elif ext in [".xml"]:
        return "xml"
    elif ext in [".xlsx", ".xls"]:
        return "excel"
    elif ext == ".parquet":
        return "parquet"
    else:
        return "unknown"


def get_spreadsheet_schema(file_path: Path, logger: logging.Logger) -> dict:
    """Extract schema information from spreadsheet files using pandas."""
    if not HAS_PANDAS:
        return {}
    
    try:
        ext = file_path.suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(file_path, nrows=100)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path, nrows=100)
        elif ext == ".parquet":
            df = pd.read_parquet(file_path).head(100)
        else:
            return {}
        
        schema = {
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "row_count_sample": len(df),
            "null_counts": df.isnull().sum().to_dict(),
            "unique_counts": {col: df[col].nunique() for col in df.columns},
            "sample_values": {col: df[col].dropna().head(3).tolist() for col in df.columns}
        }
        
        # Detect likely foreign keys (columns ending in _id, _code, etc.)
        schema["likely_foreign_keys"] = [
            col for col in df.columns 
            if any(col.lower().endswith(suffix) for suffix in ["_id", "_code", "_key", "_fk"])
        ]
        
        # Detect likely lookup tables (few unique values relative to rows)
        schema["likely_categorical"] = [
            col for col in df.columns
            if df[col].nunique() < min(20, len(df) * 0.1) and df[col].dtype == 'object'
        ]
        
        return schema
    except Exception as e:
        logger.warning(f"Could not extract schema from {file_path.name}: {e}")
        return {}


def sample_file(file_path: Path, max_lines: int = 100, max_bytes: int = 50000) -> str:
    """Read a sample from a file (first N lines or max bytes)."""
    try:
        content = []
        bytes_read = 0
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f):
                if i >= max_lines or bytes_read >= max_bytes:
                    break
                content.append(line)
                bytes_read += len(line.encode('utf-8'))
        
        return ''.join(content)
    except Exception as e:
        return f"[Error reading file: {e}]"


def gather_file_samples(input_dir: Path, logger: logging.Logger) -> dict:
    """Gather samples from all files in the input directory."""
    samples = {}
    
    for file_path in sorted(input_dir.iterdir()):
        if file_path.is_file() and not file_path.name.startswith('.'):
            logger.info(f"Sampling: {file_path.name}")
            file_format = detect_file_format(file_path)
            sample = sample_file(file_path)
            file_size = file_path.stat().st_size
            
            file_info = {
                "format": file_format,
                "size_bytes": file_size,
                "sample": sample
            }
            
            # Add schema info for spreadsheet files
            if file_format in ["csv", "excel", "parquet"]:
                schema = get_spreadsheet_schema(file_path, logger)
                if schema:
                    file_info["schema"] = schema
                    logger.info(f"  Schema: {len(schema.get('columns', []))} columns, "
                               f"{len(schema.get('likely_foreign_keys', []))} likely FKs")
            
            samples[file_path.name] = file_info
    
    return samples


def format_samples_for_prompt(samples: dict) -> str:
    """Format file samples for the LLM prompt."""
    parts = []
    for filename, info in samples.items():
        size_kb = info["size_bytes"] / 1024
        parts.append(f"=== FILE: {filename} ===")
        parts.append(f"Format: {info['format']}, Size: {size_kb:.1f} KB")
        
        # Add schema info if available (for spreadsheets)
        if "schema" in info:
            schema = info["schema"]
            parts.append(f"Columns ({len(schema['columns'])}): {', '.join(schema['columns'][:20])}")
            if len(schema['columns']) > 20:
                parts.append(f"  ... and {len(schema['columns']) - 20} more columns")
            if schema.get("likely_foreign_keys"):
                parts.append(f"Likely foreign keys: {', '.join(schema['likely_foreign_keys'])}")
            if schema.get("likely_categorical"):
                parts.append(f"Likely categorical: {', '.join(schema['likely_categorical'][:10])}")
            # Show sample values for key columns
            parts.append("Sample values:")
            for col in list(schema.get("sample_values", {}).keys())[:8]:
                vals = schema["sample_values"][col][:3]
                parts.append(f"  {col}: {vals}")
        
        parts.append("Sample content:")
        parts.append(info["sample"][:5000])  # Limit sample size in prompt
        parts.append("")
    return "\n".join(parts)


def call_llm(prompt: str, settings: dict, logger: logging.Logger) -> str:
    """Call the LLM API to analyze the data."""
    llm_config = settings["llm"]["analysis"]
    endpoint = llm_config["endpoint"]
    model = llm_config["model"]
    
    logger.info(f"Calling LLM: {model} at {endpoint}")
    logger.debug(f"Prompt length: {len(prompt)} chars")
    
    # Use OpenAI-compatible API
    url = f"{endpoint}/chat/completions"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 2048
    }
    
    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        logger.info(f"LLM response received: {len(content)} chars")
        return content
    except requests.exceptions.RequestException as e:
        logger.error(f"LLM API error: {e}")
        raise


def parse_llm_response(response: str, logger: logging.Logger) -> dict:
    """Parse the JSON response from the LLM."""
    # Try to extract JSON from the response
    try:
        # Look for JSON block in markdown
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
        else:
            # Try to parse the whole response as JSON
            json_str = response.strip()
        
        result = json.loads(json_str)
        logger.info(f"Parsed analysis: {len(result.get('entity_types', []))} entity types, {len(result.get('files', []))} files")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"Response was: {response[:500]}...")
        raise ValueError(f"LLM returned invalid JSON: {e}")


def estimate_chunks(samples: dict, chunk_token_size: int = 512) -> int:
    """Estimate total chunks based on file sizes."""
    total_bytes = sum(info["size_bytes"] for info in samples.values())
    # Rough estimate: 4 chars per token, chunk_token_size tokens per chunk
    chars_per_chunk = chunk_token_size * 4
    estimated_chunks = total_bytes / chars_per_chunk
    return int(estimated_chunks)


def analyze(input_dir: Path, output_file: Path, settings: dict, logger: logging.Logger) -> dict:
    """Main analysis function."""
    logger.info(f"Analyzing data in: {input_dir}")
    
    # Gather file samples
    samples = gather_file_samples(input_dir, logger)
    if not samples:
        raise ValueError(f"No files found in {input_dir}")
    
    logger.info(f"Found {len(samples)} files")
    
    # Load prompt template and format with samples
    script_dir = Path(__file__).parent
    prompt_template = load_prompt_template(script_dir / "prompts")
    formatted_samples = format_samples_for_prompt(samples)
    prompt = prompt_template.replace("{file_samples}", formatted_samples)
    
    # Call LLM
    response = call_llm(prompt, settings, logger)
    
    # Parse response
    analysis = parse_llm_response(response, logger)
    
    # Add metadata
    analysis["_metadata"] = {
        "input_dir": str(input_dir),
        "analyzed_at": datetime.now().isoformat(),
        "file_count": len(samples),
        "estimated_chunks": estimate_chunks(samples, settings["ragflow"]["chunk_token_num"]),
        "files_info": {name: {"size_bytes": info["size_bytes"], "format": info["format"]} 
                       for name, info in samples.items()}
    }
    
    # Estimate KG time
    est_chunks = analysis["_metadata"]["estimated_chunks"]
    time_per_chunk = settings["kg"]["time_per_chunk_minutes"]
    est_hours = (est_chunks * time_per_chunk) / 60
    analysis["_metadata"]["estimated_kg_hours"] = round(est_hours, 1)
    
    if est_hours > settings["kg"]["warn_time_hours"]:
        logger.warning(f"⚠️  Estimated KG time: {est_hours:.1f} hours for {est_chunks} chunks")
        logger.warning("Consider splitting large files or processing in batches")
    
    # Save analysis
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    logger.info(f"Analysis saved to: {output_file}")
    
    return analysis


def main():
    parser = argparse.ArgumentParser(description="Analyze data files for RAGFlow KG ingestion")
    parser.add_argument("--input", "-i", required=True, help="Input directory containing data files")
    parser.add_argument("--output", "-o", default=None, help="Output JSON file (default: config/analysis_output.json)")
    parser.add_argument("--config", "-c", default=None, help="Config file (default: config/settings.yaml)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    input_dir = Path(args.input).resolve()
    output_file = Path(args.output) if args.output else script_dir / "config" / "analysis_output.json"
    config_file = Path(args.config) if args.config else script_dir / "config" / "settings.yaml"
    
    # Setup logging
    logger = setup_logging(script_dir / "logs")
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Validate inputs
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)
    
    if not config_file.exists():
        logger.error(f"Config file not found: {config_file}")
        sys.exit(1)
    
    # Load settings
    settings = load_settings(config_file)
    
    # Run analysis
    try:
        analysis = analyze(input_dir, output_file, settings, logger)
        
        # Print summary
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"Entity types: {', '.join(analysis.get('entity_types', []))}")
        print(f"Files analyzed: {len(analysis.get('files', []))}")
        print(f"Lookup tables: {len(analysis.get('lookup_tables', []))}")
        print(f"Estimated chunks: {analysis['_metadata']['estimated_chunks']}")
        print(f"Estimated KG time: {analysis['_metadata']['estimated_kg_hours']} hours")
        print(f"\nOutput saved to: {output_file}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
