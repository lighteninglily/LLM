#!/usr/bin/env python3
"""
Model Manager for Local AI Server
Helps select, download, and configure LLM models.
"""

import json
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

CONFIG_FILE = Path.home() / ".local-ai-server" / "config.json"

# =============================================================================
# Model Database
# =============================================================================

@dataclass
class ModelInfo:
    id: str
    name: str
    size_gb: float
    vram_required_gb: float
    min_gpus: int
    quantization: str
    description: str
    use_case: str
    hf_gated: bool = False


MODELS = [
    # 32B Class - Optimal for RTX 5090 (32GB VRAM)
    ModelInfo(
        id="Qwen/Qwen3-32B-Instruct",
        name="Qwen3 32B Instruct (2026 SOTA)",
        size_gb=18,
        vram_required_gb=22,
        min_gpus=1,
        quantization="awq",
        description="Top-tier 2026 model, excellent reasoning, multilingual, 128k context",
        use_case="General purpose, reasoning, analysis, multilingual",
        hf_gated=False
    ),
    ModelInfo(
        id="Qwen/Qwen3-Coder-32B",
        name="Qwen3 Coder 32B (2026 Best Coding)",
        size_gb=18,
        vram_required_gb=22,
        min_gpus=1,
        quantization="awq",
        description="SOTA coding model for 2026, agentic capabilities",
        use_case="Coding, debugging, code generation, SWE agents",
        hf_gated=False
    ),
    
    # 27B Class - Highly efficient
    ModelInfo(
        id="google/gemma-3-27b",
        name="Gemma 3 27B (2026)",
        size_gb=15,
        vram_required_gb=18,
        min_gpus=1,
        quantization="awq",
        description="Google's latest, excellent performance-per-watt, strong reasoning",
        use_case="General purpose, efficient deployment",
        hf_gated=False
    ),
    
    # 70B Class - Q4 quantized for single RTX 5090
    ModelInfo(
        id="casperhansen/llama-3.3-70b-instruct-awq",
        name="Llama 3.3 70B Instruct (AWQ)",
        size_gb=37,
        vram_required_gb=30,
        min_gpus=1,
        quantization="awq",
        description="Meta's latest 70B, 128k context, high quality but tight VRAM fit",
        use_case="High-quality general purpose, tool use",
        hf_gated=True
    ),
    
    # 16B Class - Specialized coding
    ModelInfo(
        id="deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
        name="DeepSeek Coder V2 Lite 16B",
        size_gb=9,
        vram_required_gb=12,
        min_gpus=1,
        quantization="awq",
        description="Excellent specialized coding model, 300+ languages",
        use_case="Code generation, completion, refactoring",
        hf_gated=False
    ),
    
    # 14B Class - Balanced
    ModelInfo(
        id="Qwen/Qwen3-14B-Instruct",
        name="Qwen3 14B Instruct",
        size_gb=8,
        vram_required_gb=11,
        min_gpus=1,
        quantization="awq",
        description="Balanced performance, good quality at smaller size",
        use_case="General purpose, resource-efficient",
        hf_gated=False
    ),
    ModelInfo(
        id="mistralai/Ministral-14B-2507",
        name="Ministral 14B (2026)",
        size_gb=8,
        vram_required_gb=11,
        min_gpus=1,
        quantization="awq",
        description="Mistral's edge model with vision capabilities",
        use_case="General purpose, multimodal",
        hf_gated=False
    ),
    
    # 8B Class - Fast and efficient
    ModelInfo(
        id="Qwen/Qwen3-8B-Instruct",
        name="Qwen3 8B Instruct",
        size_gb=5,
        vram_required_gb=7,
        min_gpus=1,
        quantization="awq",
        description="Fast 8B model with strong performance",
        use_case="General purpose, fast responses",
        hf_gated=False
    ),
    ModelInfo(
        id="google/gemma-3-12b",
        name="Gemma 3 12B (2026)",
        size_gb=7,
        vram_required_gb=9,
        min_gpus=1,
        quantization="awq",
        description="Google's efficient mid-size model",
        use_case="General purpose, balanced",
        hf_gated=False
    ),
    
    # 7B Class - Maximum speed
    ModelInfo(
        id="mistralai/Mistral-Small-3.2-Instruct",
        name="Mistral Small 3.2 7B (2026)",
        size_gb=4,
        vram_required_gb=6,
        min_gpus=1,
        quantization="awq",
        description="Latest Mistral small model, very fast",
        use_case="Fast responses, high throughput",
        hf_gated=False
    ),
    ModelInfo(
        id="google/gemma-3-4b",
        name="Gemma 3 4B (2026)",
        size_gb=3,
        vram_required_gb=5,
        min_gpus=1,
        quantization="awq",
        description="Smallest Gemma 3, excellent for testing and edge deployment",
        use_case="Testing, edge deployment, rapid prototyping",
        hf_gated=False
    ),
]


def get_model_by_id(model_id: str) -> Optional[ModelInfo]:
    """Find a model by its ID."""
    for model in MODELS:
        if model.id == model_id:
            return model
    return None


def list_models(gpu_count: int = 2, total_vram_gb: float = 48):
    """List models compatible with the system."""
    print("\n" + "=" * 70)
    print("AVAILABLE MODELS")
    print("=" * 70)
    print(f"System: {gpu_count} GPU(s), {total_vram_gb:.0f} GB total VRAM\n")
    
    compatible = []
    incompatible = []
    
    for model in MODELS:
        if model.min_gpus <= gpu_count and model.vram_required_gb <= total_vram_gb:
            compatible.append(model)
        else:
            incompatible.append(model)
    
    print("✅ COMPATIBLE MODELS:\n")
    for i, model in enumerate(compatible, 1):
        gated = " [GATED]" if model.hf_gated else ""
        print(f"  {i}. {model.name}{gated}")
        print(f"     ID: {model.id}")
        print(f"     Size: {model.size_gb:.0f} GB | VRAM: ~{model.vram_required_gb:.0f} GB | GPUs: {model.min_gpus}+")
        print(f"     Use: {model.use_case}")
        print()
    
    if incompatible:
        print("-" * 70)
        print("❌ INCOMPATIBLE (need more VRAM/GPUs):\n")
        for model in incompatible:
            print(f"  • {model.name} (needs {model.vram_required_gb:.0f} GB, {model.min_gpus}+ GPUs)")
    
    return compatible


def select_model_interactive(gpu_count: int = 2, total_vram_gb: float = 48) -> Optional[ModelInfo]:
    """Interactive model selection."""
    compatible = list_models(gpu_count, total_vram_gb)
    
    if not compatible:
        print("\n❌ No compatible models found for your system!")
        return None
    
    print("-" * 70)
    choice = input("\nEnter model number (or 'q' to quit): ").strip()
    
    if choice.lower() == 'q':
        return None
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(compatible):
            return compatible[idx]
        else:
            print("Invalid selection")
            return None
    except ValueError:
        print("Invalid input")
        return None


def update_config_model(model: ModelInfo):
    """Update the configuration with the selected model."""
    if not CONFIG_FILE.exists():
        print(f"❌ Config file not found: {CONFIG_FILE}")
        print("   Run 'python3 deploy.py install' first")
        return False
    
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    
    config["llm"]["model"] = model.id
    config["llm"]["quantization"] = model.quantization
    config["llm"]["tensor_parallel_size"] = model.min_gpus
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Config updated with model: {model.name}")
    print(f"   File: {CONFIG_FILE}")
    
    # Also need to update docker-compose
    print("\n⚠️  You need to regenerate docker-compose.yml:")
    print("   python3 deploy.py install")
    print("\n   Then restart services:")
    print("   docker compose down && docker compose up -d")
    
    return True


def check_hf_token():
    """Check if HuggingFace token is configured."""
    env_file = Path.home() / ".local-ai-server" / ".env"
    
    if not env_file.exists():
        return False
    
    with open(env_file) as f:
        content = f.read()
        if "HF_TOKEN=" in content:
            # Check if it's not empty
            for line in content.split('\n'):
                if line.startswith("HF_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    return len(token) > 0
    
    return False


def download_model(model: ModelInfo):
    """Pre-download a model using huggingface-cli."""
    print(f"\n📥 Downloading model: {model.name}")
    print(f"   Size: ~{model.size_gb:.0f} GB")
    print(f"   This may take a while...\n")
    
    if model.hf_gated and not check_hf_token():
        print("⚠️  This is a gated model. You need to:")
        print("   1. Get token from: https://huggingface.co/settings/tokens")
        print("   2. Accept license at: https://huggingface.co/" + model.id.split('/')[0])
        print("   3. Add token to ~/.local-ai-server/.env")
        
        proceed = input("\nContinue anyway? [y/N]: ").strip().lower()
        if proceed != 'y':
            return False
    
    # Use huggingface-cli to download
    cmd = f"huggingface-cli download {model.id} --local-dir-use-symlinks False"
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"\n✅ Model downloaded: {model.name}")
        return True
    except subprocess.CalledProcessError:
        print(f"\n❌ Download failed. Check your HF_TOKEN and internet connection.")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Model Manager for Local AI Server")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available models")
    list_parser.add_argument("--gpus", type=int, default=2, help="Number of GPUs")
    list_parser.add_argument("--vram", type=float, default=48, help="Total VRAM in GB")
    
    # Select command
    select_parser = subparsers.add_parser("select", help="Interactively select a model")
    select_parser.add_argument("--gpus", type=int, default=2, help="Number of GPUs")
    select_parser.add_argument("--vram", type=float, default=48, help="Total VRAM in GB")
    
    # Set command
    set_parser = subparsers.add_parser("set", help="Set a specific model by ID")
    set_parser.add_argument("model_id", help="Model ID (e.g., TheBloke/Llama-2-70B-Chat-AWQ)")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Pre-download a model")
    download_parser.add_argument("model_id", help="Model ID to download")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show info about a model")
    info_parser.add_argument("model_id", help="Model ID")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_models(args.gpus, args.vram)
    
    elif args.command == "select":
        model = select_model_interactive(args.gpus, args.vram)
        if model:
            confirm = input(f"\nSet '{model.name}' as the active model? [Y/n]: ").strip().lower()
            if confirm != 'n':
                update_config_model(model)
    
    elif args.command == "set":
        model = get_model_by_id(args.model_id)
        if model:
            update_config_model(model)
        else:
            print(f"❌ Model not found: {args.model_id}")
            print("   Use 'python3 models.py list' to see available models")
    
    elif args.command == "download":
        model = get_model_by_id(args.model_id)
        if model:
            download_model(model)
        else:
            print(f"❌ Model not found in database: {args.model_id}")
            print("   Attempting direct download...")
            subprocess.run(f"huggingface-cli download {args.model_id}", shell=True)
    
    elif args.command == "info":
        model = get_model_by_id(args.model_id)
        if model:
            print(f"\n{'='*50}")
            print(f"Model: {model.name}")
            print(f"{'='*50}")
            print(f"ID:            {model.id}")
            print(f"Size:          {model.size_gb:.0f} GB")
            print(f"VRAM Required: {model.vram_required_gb:.0f} GB")
            print(f"Min GPUs:      {model.min_gpus}")
            print(f"Quantization:  {model.quantization}")
            print(f"Gated:         {'Yes' if model.hf_gated else 'No'}")
            print(f"\nDescription: {model.description}")
            print(f"Use Case:    {model.use_case}")
        else:
            print(f"❌ Model not found: {args.model_id}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
