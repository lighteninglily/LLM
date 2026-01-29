#!/usr/bin/env python3
"""
RAGFlow Automation Toolkit - Main Orchestrator
Runs the complete pipeline: Analyze → Transform → Setup RAGFlow
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import requests
import yaml

# Setup logging
def setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"main_{timestamp}.log"
    
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


def check_vllm(settings: dict, logger: logging.Logger) -> bool:
    """Check vLLM is reachable and has sufficient context length."""
    endpoint = settings["llm"]["analysis"]["endpoint"]
    
    try:
        # Check models endpoint
        response = requests.get(f"{endpoint}/models", timeout=10)
        if response.status_code != 200:
            logger.error(f"vLLM not responding at {endpoint}")
            return False
        
        models = response.json()
        logger.info(f"✓ vLLM reachable at {endpoint}")
        
        # Try to check context length via a test request
        # Note: vLLM doesn't expose max_model_len directly via API
        # We'll warn but not fail
        logger.info("  Note: Ensure vLLM has VLLM_ALLOW_LONG_MAX_MODEL_LEN=1 and MAX_MODEL_LEN=65536")
        
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ vLLM check failed: {e}")
        return False


def check_ragflow(settings: dict, logger: logging.Logger) -> bool:
    """Check RAGFlow API is reachable and API key is valid."""
    endpoint = settings["ragflow"]["endpoint"]
    api_key = settings["ragflow"]["api_key"]
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{endpoint}/api/v1/datasets", headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                logger.info(f"✓ RAGFlow API reachable and authenticated")
                return True
            else:
                logger.error(f"✗ RAGFlow API error: {result}")
                return False
        else:
            logger.error(f"✗ RAGFlow returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ RAGFlow check failed: {e}")
        return False


def check_ollama(settings: dict, logger: logging.Logger) -> bool:
    """Check Ollama is reachable for embeddings."""
    # Extract Ollama endpoint from embedding model config
    # Assuming Ollama runs on default port
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            logger.info("✓ Ollama reachable for embeddings")
            return True
        else:
            logger.warning("⚠ Ollama may not be running (embeddings might fail)")
            return True  # Don't fail, RAGFlow might handle this
            
    except requests.exceptions.RequestException:
        logger.warning("⚠ Could not reach Ollama at localhost:11434")
        return True  # Don't fail


def estimate_processing(input_dir: Path, settings: dict, logger: logging.Logger) -> dict:
    """Estimate processing time and chunk counts."""
    total_bytes = 0
    file_count = 0
    
    for file_path in input_dir.iterdir():
        if file_path.is_file() and not file_path.name.startswith('.'):
            total_bytes += file_path.stat().st_size
            file_count += 1
    
    # Estimate chunks: ~2KB per chunk on average
    chunk_token_num = settings["ragflow"]["chunk_token_num"]
    chars_per_chunk = chunk_token_num * 4
    estimated_chunks = int(total_bytes / chars_per_chunk)
    
    # Estimate KG time
    time_per_chunk = settings["kg"]["time_per_chunk_minutes"]
    estimated_hours = (estimated_chunks * time_per_chunk) / 60
    
    estimates = {
        "file_count": file_count,
        "total_size_mb": total_bytes / (1024 * 1024),
        "estimated_chunks": estimated_chunks,
        "estimated_kg_hours": round(estimated_hours, 1)
    }
    
    return estimates


def run_preflight_checks(input_dir: Path, settings: dict, logger: logging.Logger) -> bool:
    """Run all preflight checks before processing."""
    print("\n" + "="*60)
    print("PREFLIGHT CHECKS")
    print("="*60)
    
    all_passed = True
    
    # Check input directory
    if not input_dir.exists():
        logger.error(f"✗ Input directory not found: {input_dir}")
        return False
    
    files = list(input_dir.iterdir())
    files = [f for f in files if f.is_file() and not f.name.startswith('.')]
    if not files:
        logger.error(f"✗ No files found in {input_dir}")
        return False
    logger.info(f"✓ Input directory: {len(files)} files found")
    
    # Check vLLM
    if not check_vllm(settings, logger):
        all_passed = False
    
    # Check RAGFlow
    if not check_ragflow(settings, logger):
        all_passed = False
    
    # Check Ollama
    check_ollama(settings, logger)
    
    # Estimate processing
    estimates = estimate_processing(input_dir, settings, logger)
    
    print("\n" + "-"*40)
    print("ESTIMATES")
    print("-"*40)
    print(f"Files: {estimates['file_count']}")
    print(f"Total size: {estimates['total_size_mb']:.1f} MB")
    print(f"Estimated chunks: {estimates['estimated_chunks']}")
    print(f"Estimated KG time: {estimates['estimated_kg_hours']} hours")
    
    # Warn if large dataset
    if estimates['estimated_chunks'] > settings["kg"]["max_chunks_per_kb"]:
        logger.warning(f"⚠ Large dataset: {estimates['estimated_chunks']} chunks exceeds recommended {settings['kg']['max_chunks_per_kb']}")
        logger.warning("  Consider splitting into multiple knowledge bases")
    
    if estimates['estimated_kg_hours'] > settings["kg"]["warn_time_hours"]:
        logger.warning(f"⚠ Long processing time: {estimates['estimated_kg_hours']} hours")
    
    print("="*60 + "\n")
    
    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="RAGFlow Automation Toolkit - Ingest data with Knowledge Graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --input /path/to/data --name "My Dataset"
  python main.py --input ./data --name "Test KB" --analyze-only
  python main.py --input ./data --name "Test KB" --skip-transform
        """
    )
    
    parser.add_argument("--input", "-i", required=True, help="Input directory containing data files")
    parser.add_argument("--name", "-n", required=True, help="Knowledge Base name")
    parser.add_argument("--output", "-o", default="./output", help="Transform output directory")
    parser.add_argument("--config", "-c", default=None, help="Config file path")
    parser.add_argument("--analyze-only", action="store_true", help="Run only analysis step")
    parser.add_argument("--skip-transform", action="store_true", help="Skip transformation step")
    parser.add_argument("--skip-kg", action="store_true", help="Skip KG generation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()
    config_file = Path(args.config) if args.config else script_dir / "config" / "settings.yaml"
    analysis_file = script_dir / "config" / "analysis_output.json"
    
    # Setup logging
    logger = setup_logging(script_dir / "logs")
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    print("\n" + "="*60)
    print("RAGFLOW AUTOMATION TOOLKIT")
    print("="*60)
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"KB Name: {args.name}")
    print("="*60)
    
    # Load settings
    if not config_file.exists():
        logger.error(f"Config file not found: {config_file}")
        sys.exit(1)
    
    settings = load_settings(config_file)
    
    # Run preflight checks
    if not run_preflight_checks(input_dir, settings, logger):
        logger.error("Preflight checks failed")
        sys.exit(1)
    
    # Confirm with user
    if not args.yes:
        response = input("Proceed? [y/N]: ").strip().lower()
        if response != 'y':
            print("Aborted.")
            sys.exit(0)
    
    # ========== STEP 1: ANALYZE ==========
    print("\n" + "="*60)
    print("STEP 1: ANALYZE")
    print("="*60)
    
    from analyze import analyze, load_prompt_template, gather_file_samples
    
    try:
        # Import and run analysis
        from analyze import analyze as run_analyze
        analysis = run_analyze(input_dir, analysis_file, settings, logger)
        
        print(f"\nEntity types detected: {', '.join(analysis.get('entity_types', []))}")
        print(f"Files to transform: {sum(1 for f in analysis.get('files', []) if f.get('transform'))}")
        print(f"Analysis saved to: {analysis_file}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)
    
    if args.analyze_only:
        print("\n--analyze-only flag set. Stopping here.")
        sys.exit(0)
    
    # ========== STEP 2: TRANSFORM ==========
    if not args.skip_transform:
        print("\n" + "="*60)
        print("STEP 2: TRANSFORM")
        print("="*60)
        
        # Check if any files need transformation
        needs_transform = any(f.get("transform") for f in analysis.get("files", []))
        
        if needs_transform:
            try:
                from transform import transform as run_transform
                results = run_transform(input_dir, output_dir, analysis, settings, logger)
                
                print(f"\nTransformed: {len(results['transformed'])} files")
                print(f"Copied: {len(results['copied'])} files")
                print(f"Output: {output_dir}")
                
            except Exception as e:
                logger.error(f"Transformation failed: {e}")
                sys.exit(1)
        else:
            print("No files need transformation. Copying to output...")
            output_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            for file_path in input_dir.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    shutil.copy2(file_path, output_dir / file_path.name)
            print(f"Copied all files to: {output_dir}")
    else:
        print("\n--skip-transform flag set. Using input directory directly.")
        output_dir = input_dir
    
    # ========== STEP 3: SETUP RAGFLOW ==========
    print("\n" + "="*60)
    print("STEP 3: SETUP RAGFLOW")
    print("="*60)
    
    try:
        from setup_ragflow import setup_ragflow as run_setup
        result = run_setup(output_dir, args.name, analysis, settings, logger, args.skip_kg)
        
        print("\n" + "="*60)
        print("✓ COMPLETE")
        print("="*60)
        print(f"Knowledge Base: {result['kb_name']}")
        print(f"KB ID: {result['kb_id']}")
        print(f"Documents: {result['documents_uploaded']}")
        if result.get('chat_id'):
            print(f"Chat Assistant: {result['chat_id']}")
        print(f"\nRAGFlow UI: {settings['ragflow']['endpoint']}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"RAGFlow setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
