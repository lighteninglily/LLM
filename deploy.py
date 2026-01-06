#!/usr/bin/env python3
"""
Local AI Server Deployment Tool
Automates the setup of a local AI server with RAG capabilities.

Architecture:
- vLLM: Multi-GPU LLM inference (tensor parallelism for 70B models)
- AnythingLLM: RAG pipeline, document ingestion, web UI
- ChromaDB: Vector database (via AnythingLLM)

Usage:
    python3 deploy.py detect          # Hardware detection
    python3 deploy.py install         # Full installation
    python3 deploy.py install --auto  # Unattended installation
    python3 deploy.py serve           # Start all services
    python3 deploy.py status          # Check system status
"""

import subprocess
import sys
import os
import json
import shutil
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# =============================================================================
# Configuration
# =============================================================================

BASE_DIR = Path.home() / ".local-ai-server"
CONFIG_FILE = BASE_DIR / "config.json"
LOG_DIR = BASE_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

DEFAULT_CONFIG = {
    "llm": {
        "model": "Qwen/Qwen3-32B-Instruct",
        "backend": "vllm",
        "tensor_parallel_size": 1,
        "max_model_len": 4096,
        "gpu_memory_utilization": 0.85,
        "quantization": "awq"
    },
    "embedding": {
        "model": "BAAI/bge-large-en-v1.5",
        "device": "cpu"
    },
    "server": {
        "vllm_host": "0.0.0.0",
        "vllm_port": 8000,
        "anythingllm_port": 3001
    },
    "paths": {
        "base_dir": str(BASE_DIR),
        "models_dir": str(MODELS_DIR),
        "data_dir": str(DATA_DIR)
    }
}

# =============================================================================
# Hardware Detection
# =============================================================================

@dataclass
class GPUInfo:
    index: int
    name: str
    memory_total_mb: int
    memory_free_mb: int
    driver_version: str
    cuda_version: str
    compute_capability: str

@dataclass
class SystemInfo:
    os_name: str
    os_version: str
    cpu_model: str
    cpu_cores: int
    ram_total_gb: float
    ram_available_gb: float
    gpus: List[GPUInfo]
    cuda_available: bool
    docker_available: bool
    nvidia_docker_available: bool


def run_command(cmd: str, capture: bool = True, check: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        return e


def detect_gpus() -> List[GPUInfo]:
    """Detect NVIDIA GPUs using nvidia-smi."""
    gpus = []
    
    result = run_command(
        "nvidia-smi --query-gpu=index,name,memory.total,memory.free,driver_version "
        "--format=csv,noheader,nounits"
    )
    
    if result.returncode != 0:
        return gpus
    
    # Get CUDA version
    cuda_result = run_command("nvidia-smi --query-gpu=driver_version --format=csv,noheader")
    cuda_version = "Unknown"
    nvcc_result = run_command("nvcc --version")
    if nvcc_result.returncode == 0:
        for line in nvcc_result.stdout.split('\n'):
            if 'release' in line.lower():
                parts = line.split('release')
                if len(parts) > 1:
                    cuda_version = parts[1].split(',')[0].strip()
                    break
    
    for line in result.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 5:
            # Get compute capability
            cc_result = run_command(
                f"nvidia-smi --query-gpu=compute_cap --format=csv,noheader -i {parts[0]}"
            )
            compute_cap = cc_result.stdout.strip() if cc_result.returncode == 0 else "Unknown"
            
            gpus.append(GPUInfo(
                index=int(parts[0]),
                name=parts[1],
                memory_total_mb=int(float(parts[2])),
                memory_free_mb=int(float(parts[3])),
                driver_version=parts[4],
                cuda_version=cuda_version,
                compute_capability=compute_cap
            ))
    
    return gpus


def detect_system() -> SystemInfo:
    """Detect full system information."""
    
    # OS Info
    os_name = "Unknown"
    os_version = "Unknown"
    
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("NAME="):
                    os_name = line.split("=")[1].strip().strip('"')
                elif line.startswith("VERSION_ID="):
                    os_version = line.split("=")[1].strip().strip('"')
    
    # CPU Info
    cpu_model = "Unknown"
    cpu_cores = os.cpu_count() or 0
    
    if os.path.exists("/proc/cpuinfo"):
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    cpu_model = line.split(":")[1].strip()
                    break
    
    # RAM Info
    ram_total_gb = 0.0
    ram_available_gb = 0.0
    
    if os.path.exists("/proc/meminfo"):
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    ram_total_gb = int(line.split()[1]) / 1024 / 1024
                elif line.startswith("MemAvailable:"):
                    ram_available_gb = int(line.split()[1]) / 1024 / 1024
    
    # GPU Info
    gpus = detect_gpus()
    
    # Docker check
    docker_result = run_command("docker --version")
    docker_available = docker_result.returncode == 0
    
    # NVIDIA Docker check
    nvidia_docker_result = run_command("docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi")
    nvidia_docker_available = nvidia_docker_result.returncode == 0
    
    return SystemInfo(
        os_name=os_name,
        os_version=os_version,
        cpu_model=cpu_model,
        cpu_cores=cpu_cores,
        ram_total_gb=round(ram_total_gb, 1),
        ram_available_gb=round(ram_available_gb, 1),
        gpus=gpus,
        cuda_available=len(gpus) > 0,
        docker_available=docker_available,
        nvidia_docker_available=nvidia_docker_available
    )


def print_system_report(info: SystemInfo):
    """Print a formatted system report."""
    print("\n" + "=" * 60)
    print("SYSTEM DETECTION REPORT")
    print("=" * 60)
    
    print(f"\n📦 Operating System: {info.os_name} {info.os_version}")
    print(f"🖥️  CPU: {info.cpu_model} ({info.cpu_cores} cores)")
    print(f"🧠 RAM: {info.ram_available_gb:.1f} GB available / {info.ram_total_gb:.1f} GB total")
    
    print(f"\n🐳 Docker: {'✅ Available' if info.docker_available else '❌ Not installed'}")
    print(f"🎮 NVIDIA Docker: {'✅ Available' if info.nvidia_docker_available else '❌ Not configured'}")
    
    if info.gpus:
        print(f"\n🎯 GPUs Detected: {len(info.gpus)}")
        total_vram = sum(g.memory_total_mb for g in info.gpus)
        print(f"💾 Total VRAM: {total_vram / 1024:.1f} GB")
        
        for gpu in info.gpus:
            print(f"\n  GPU {gpu.index}: {gpu.name}")
            print(f"    Memory: {gpu.memory_free_mb / 1024:.1f} GB free / {gpu.memory_total_mb / 1024:.1f} GB total")
            print(f"    Driver: {gpu.driver_version}")
            print(f"    CUDA: {gpu.cuda_version}")
            print(f"    Compute Capability: {gpu.compute_capability}")
    else:
        print("\n⚠️  No NVIDIA GPUs detected!")
    
    # Recommendations
    print("\n" + "-" * 60)
    print("RECOMMENDATIONS")
    print("-" * 60)
    
    if len(info.gpus) >= 2:
        total_vram = sum(g.memory_total_mb for g in info.gpus)
        if total_vram >= 45000:
            print("Sufficient VRAM for 70B model (4-bit quantized)")
            print("   Recommended: Llama-3.3-70B-AWQ with tensor_parallel_size=2")
        elif total_vram >= 24000:
            print("Limited VRAM - recommend 32B or smaller model")
            print("   Recommended: Qwen3-32B-Instruct or Gemma-3-27B")
    elif len(info.gpus) == 1:
        if info.gpus[0].memory_total_mb >= 30000:
            print("RTX 5090 detected - excellent for 32B models")
            print("   Recommended: Qwen3-32B-Instruct or Gemma-3-27B")
        elif info.gpus[0].memory_total_mb >= 20000:
            print("Single GPU with good VRAM")
            print("   Recommended: Qwen3-14B-Instruct or Gemma-3-12B")
        else:
            print("Limited VRAM - recommend smaller model")
            print("   Recommended: Qwen3-8B-Instruct")
    
    if not info.docker_available:
        print("\n⚠️  Docker not installed - required for deployment")
        print("   Run: curl -fsSL https://get.docker.com | sh")
    
    if info.docker_available and not info.nvidia_docker_available:
        print("\n⚠️  NVIDIA Container Toolkit not configured")
        print("   Required for GPU access in Docker containers")
    
    print("\n" + "=" * 60)


# =============================================================================
# Installation Functions
# =============================================================================

class Installer:
    def __init__(self, auto_mode: bool = False):
        self.auto_mode = auto_mode
        self.system_info: Optional[SystemInfo] = None
        
    def log(self, message: str, level: str = "INFO"):
        """Print and log a message."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        prefix = {"INFO": "ℹ️ ", "SUCCESS": "✅", "WARNING": "⚠️ ", "ERROR": "❌"}
        print(f"{prefix.get(level, '')} [{timestamp}] {message}")
    
    def confirm(self, message: str, default: bool = True) -> bool:
        """Ask for confirmation (skipped in auto mode)."""
        if self.auto_mode:
            return default
        
        suffix = " [Y/n]: " if default else " [y/N]: "
        response = input(message + suffix).strip().lower()
        
        if not response:
            return default
        return response in ('y', 'yes')
    
    def run_step(self, name: str, command: str, check: bool = True) -> bool:
        """Run an installation step."""
        self.log(f"Running: {name}")
        result = run_command(command, capture=False)
        
        if result.returncode != 0:
            self.log(f"Failed: {name}", "ERROR")
            if check:
                return False
        else:
            self.log(f"Completed: {name}", "SUCCESS")
        
        return True
    
    def setup_directories(self):
        """Create required directories."""
        self.log("Setting up directories...")
        
        for directory in [BASE_DIR, LOG_DIR, MODELS_DIR, DATA_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
            self.log(f"Created: {directory}")
        
        # Save default config if not exists
        if not CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            self.log(f"Created default config: {CONFIG_FILE}")
    
    def is_wsl(self) -> bool:
        """Check if running in Windows Subsystem for Linux."""
        try:
            with open("/proc/version", "r") as f:
                return "microsoft" in f.read().lower() or "wsl" in f.read().lower()
        except FileNotFoundError:
            return False

    def install_nvidia_drivers(self) -> bool:
        """Install NVIDIA drivers if needed."""
        self.log("Checking NVIDIA drivers...")
        
        # Check for WSL
        if self.is_wsl():
            self.log("WSL environment detected. NVIDIA drivers are managed by Windows host.", "SUCCESS")
            
            # Verify basic nvidia-smi visibility
            result = run_command("nvidia-smi")
            if result.returncode != 0:
                self.log("⚠️  nvidia-smi failed. Ensure NVIDIA drivers are installed on Windows.", "WARNING")
                return self.confirm("Continue anyway?", default=False)
            return True

        result = run_command("nvidia-smi")
        if result.returncode == 0:
            self.log("NVIDIA drivers already installed", "SUCCESS")
            return True
        
        if not self.confirm("NVIDIA drivers not found. Install them?"):
            return False
        
        commands = [
            "sudo apt-get update",
            "sudo apt-get install -y ubuntu-drivers-common",
            "sudo ubuntu-drivers autoinstall"
        ]
        
        for cmd in commands:
            if not self.run_step(f"Driver install: {cmd}", cmd):
                return False
        
        self.log("NVIDIA drivers installed. REBOOT REQUIRED!", "WARNING")
        return True
    
    def install_cuda_toolkit(self) -> bool:
        """Install CUDA toolkit if needed."""
        self.log("Checking CUDA toolkit...")
        
        result = run_command("nvcc --version")
        if result.returncode == 0:
            self.log("CUDA toolkit already installed", "SUCCESS")
            return True
        
        if not self.confirm("CUDA toolkit not found. Install it?"):
            return False
        
        # Install CUDA 12.x
        commands = [
            "wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb",
            "sudo dpkg -i cuda-keyring_1.1-1_all.deb",
            "sudo apt-get update",
            "sudo apt-get install -y cuda-toolkit-12-4",
            "rm cuda-keyring_1.1-1_all.deb"
        ]
        
        for cmd in commands:
            if not self.run_step(f"CUDA install: {cmd}", cmd, check=False):
                pass  # Continue even if some steps fail
        
        # Add to PATH
        bashrc = Path.home() / ".bashrc"
        cuda_path = 'export PATH=/usr/local/cuda/bin:$PATH\nexport LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH\n'
        
        with open(bashrc, 'a') as f:
            f.write(f"\n# CUDA\n{cuda_path}")
        
        self.log("CUDA toolkit installed. Run 'source ~/.bashrc' or restart terminal", "SUCCESS")
        return True
    
    def install_docker(self) -> bool:
        """Install Docker if needed."""
        self.log("Checking Docker...")
        
        result = run_command("docker --version")
        if result.returncode == 0:
            self.log("Docker already installed", "SUCCESS")
        else:
            if not self.confirm("Docker not found. Install it?"):
                return False
            
            if not self.run_step("Install Docker", "curl -fsSL https://get.docker.com | sh"):
                return False
            
            # Add user to docker group
            user = os.environ.get("USER", "")
            if user:
                self.run_step("Add user to docker group", f"sudo usermod -aG docker {user}", check=False)
        
        return True
    
    def install_nvidia_container_toolkit(self) -> bool:
        """Install NVIDIA Container Toolkit."""
        self.log("Checking NVIDIA Container Toolkit...")
        
        # Test if it works
        result = run_command("docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi")
        if result.returncode == 0:
            self.log("NVIDIA Container Toolkit already working", "SUCCESS")
            return True
        
        if not self.confirm("NVIDIA Container Toolkit not configured. Install it?"):
            return False
        
        commands = [
            "curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg",
            'curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed \'s#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g\' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list',
            "sudo apt-get update",
            "sudo apt-get install -y nvidia-container-toolkit",
            "sudo nvidia-ctk runtime configure --runtime=docker",
            "sudo systemctl restart docker"
        ]
        
        for cmd in commands:
            self.run_step("NVIDIA Container Toolkit", cmd, check=False)
        
        self.log("NVIDIA Container Toolkit installed", "SUCCESS")
        return True
    
    def create_docker_compose(self) -> bool:
        """Create docker-compose.yml for the full stack."""
        self.log("Creating Docker Compose configuration...")
        
        # Load config
        config = DEFAULT_CONFIG
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                config = json.load(f)
        
        # Determine tensor parallel size based on detected GPUs
        tensor_parallel = config["llm"].get("tensor_parallel_size", 2)
        if self.system_info:
            tensor_parallel = min(tensor_parallel, len(self.system_info.gpus))
        
        docker_compose = f"""version: '3.8'

services:
  # vLLM - LLM Inference Server with Multi-GPU support
  vllm:
    image: vllm/vllm-openai:latest
    container_name: local-ai-vllm
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - HF_TOKEN=${{HF_TOKEN:-}}
    volumes:
      - {MODELS_DIR}:/root/.cache/huggingface
      - /dev/shm:/dev/shm
    ports:
      - "{config['server']['vllm_port']}:8000"
    command: >
      --model {config['llm']['model']}
      --tensor-parallel-size {tensor_parallel}
      --max-model-len {config['llm']['max_model_len']}
      --gpu-memory-utilization {config['llm']['gpu_memory_utilization']}
      --dtype auto
      --trust-remote-code
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 300s
    restart: unless-stopped

  # AnythingLLM - RAG + Web UI
  anythingllm:
    image: mintplexlabs/anythingllm:latest
    container_name: local-ai-anythingllm
    volumes:
      - {DATA_DIR}/anythingllm:/app/server/storage
      - {DATA_DIR}/documents:/app/server/storage/documents
    ports:
      - "{config['server']['anythingllm_port']}:3001"
    environment:
      - STORAGE_DIR=/app/server/storage
      - LLM_PROVIDER=generic-openai
      - GENERIC_OPEN_AI_BASE_PATH=http://vllm:8000/v1
      - GENERIC_OPEN_AI_MODEL_PREF={config['llm']['model'].split('/')[-1]}
      - GENERIC_OPEN_AI_MODEL_TOKEN_LIMIT={config['llm']['max_model_len']}
      - EMBEDDING_ENGINE=native
      - VECTOR_DB=lancedb
      - TTS_PROVIDER=native
      - PASSWORDLESS_AUTH=false
    depends_on:
      vllm:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/api/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

volumes:
  vllm-models:
  anythingllm-storage:

networks:
  default:
    name: local-ai-network
"""
        
        compose_file = BASE_DIR / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            f.write(docker_compose)
        
        self.log(f"Created: {compose_file}", "SUCCESS")
        return True
    
    def create_env_file(self) -> bool:
        """Create .env file for secrets."""
        env_file = BASE_DIR / ".env"
        
        if env_file.exists():
            self.log(".env file already exists, skipping", "INFO")
            return True
        
        env_content = f"""# Local AI Server Environment Variables
# Add your HuggingFace token here for gated models (e.g., Llama-2)
HF_TOKEN=

# Auto-generated vLLM API Key (do not share!)
VLLM_API_KEY={os.urandom(16).hex()}

# Optional: Anthropic API key for fallback
ANTHROPIC_API_KEY=

# Optional: OpenAI API key for fallback
OPENAI_API_KEY=
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        self.log(f"Created: {env_file}", "SUCCESS")
        self.log("Edit .env file to add your HuggingFace token for gated models", "WARNING")
        return True
    
    def create_management_scripts(self) -> bool:
        """Create helper scripts for managing the server."""
        
        # Start script
        start_script = BASE_DIR / "start.sh"
        with open(start_script, 'w') as f:
            f.write(f"""#!/bin/bash
cd {BASE_DIR}
docker compose --env-file .env up -d
echo "Services starting..."
echo "vLLM API: http://localhost:8000"
echo "AnythingLLM UI: http://localhost:3001"
echo ""
echo "Use 'docker compose logs -f' to view logs"
""")
        start_script.chmod(0o755)
        
        # Stop script
        stop_script = BASE_DIR / "stop.sh"
        with open(stop_script, 'w') as f:
            f.write(f"""#!/bin/bash
cd {BASE_DIR}
docker compose down
echo "Services stopped."
""")
        stop_script.chmod(0o755)
        
        # Status script
        status_script = BASE_DIR / "status.sh"
        with open(status_script, 'w') as f:
            f.write(f"""#!/bin/bash
cd {BASE_DIR}
echo "=== Container Status ==="
docker compose ps
echo ""
echo "=== GPU Usage ==="
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv
echo ""
echo "=== Service Health ==="
curl -s http://localhost:8000/health && echo " vLLM: OK" || echo "vLLM: DOWN"
curl -s http://localhost:3001/api/ping && echo " AnythingLLM: OK" || echo "AnythingLLM: DOWN"
""")
        status_script.chmod(0o755)
        
        # Logs script
        logs_script = BASE_DIR / "logs.sh"
        with open(logs_script, 'w') as f:
            f.write(f"""#!/bin/bash
cd {BASE_DIR}
docker compose logs -f "$@"
""")
        logs_script.chmod(0o755)
        
        self.log("Created management scripts in ~/.local-ai-server/", "SUCCESS")
        return True
    
    def pull_images(self) -> bool:
        """Pre-pull Docker images."""
        self.log("Pulling Docker images (this may take a while)...")
        
        images = [
            "vllm/vllm-openai:latest",
            "mintplexlabs/anythingllm:latest"
        ]
        
        for image in images:
            self.run_step(f"Pulling {image}", f"docker pull {image}", check=False)
        
        return True
    
    def run_full_install(self) -> bool:
        """Run the complete installation process."""
        self.log("Starting full installation...")
        
        # Detect system first
        self.system_info = detect_system()
        print_system_report(self.system_info)
        
        if not self.confirm("\nProceed with installation?"):
            return False
        
        steps = [
            ("Setup directories", self.setup_directories),
            ("Install NVIDIA drivers", self.install_nvidia_drivers),
            ("Install CUDA toolkit", self.install_cuda_toolkit),
            ("Install Docker", self.install_docker),
            ("Install NVIDIA Container Toolkit", self.install_nvidia_container_toolkit),
            ("Create Docker Compose", self.create_docker_compose),
            ("Create .env file", self.create_env_file),
            ("Create management scripts", self.create_management_scripts),
            ("Pull Docker images", self.pull_images),
        ]
        
        for name, func in steps:
            self.log(f"\n{'='*40}\n{name}\n{'='*40}")
            try:
                result = func()
                if result is False:
                    self.log(f"Step failed: {name}", "ERROR")
                    if not self.confirm("Continue anyway?"):
                        return False
            except Exception as e:
                self.log(f"Error in {name}: {e}", "ERROR")
                if not self.confirm("Continue anyway?"):
                    return False
        
        # Final summary
        print("\n" + "=" * 60)
        print("INSTALLATION COMPLETE")
        print("=" * 60)
        print(f"""
📁 Installation directory: {BASE_DIR}

🚀 To start the server:
   cd {BASE_DIR}
   ./start.sh

   Or: docker compose up -d

🌐 Access points:
   - AnythingLLM UI: http://localhost:3001
   - vLLM API: http://localhost:8000/v1

📋 Management commands:
   - Start:  {BASE_DIR}/start.sh
   - Stop:   {BASE_DIR}/stop.sh
   - Status: {BASE_DIR}/status.sh
   - Logs:   {BASE_DIR}/logs.sh

⚠️  Important:
   1. Edit {BASE_DIR}/.env to add your HuggingFace token
   2. First startup may take 10-30 minutes to download the model
   3. Check logs with: docker compose logs -f vllm
""")
        
        return True


# =============================================================================
# Service Management
# =============================================================================

def start_services():
    """Start all services."""
    os.chdir(BASE_DIR)
    subprocess.run(["docker", "compose", "--env-file", ".env", "up", "-d"])
    
    print("\n🚀 Services starting...")
    print(f"   vLLM API: http://localhost:8000")
    print(f"   AnythingLLM UI: http://localhost:3001")
    print("\n   Use 'docker compose logs -f' to monitor startup")


def stop_services():
    """Stop all services."""
    os.chdir(BASE_DIR)
    subprocess.run(["docker", "compose", "down"])
    print("Services stopped.")


def show_status():
    """Show service status."""
    os.chdir(BASE_DIR)
    
    print("=== Container Status ===")
    subprocess.run(["docker", "compose", "ps"])
    
    print("\n=== GPU Usage ===")
    subprocess.run(["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total", "--format=csv"])
    
    print("\n=== Service Health ===")
    
    import urllib.request
    
    try:
        urllib.request.urlopen("http://localhost:8000/health", timeout=5)
        print("✅ vLLM: Running")
    except:
        print("❌ vLLM: Not responding")
    
    try:
        urllib.request.urlopen("http://localhost:3001/api/ping", timeout=5)
        print("✅ AnythingLLM: Running")
    except:
        print("❌ AnythingLLM: Not responding")


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Local AI Server Deployment Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 deploy.py detect          # Detect hardware
  python3 deploy.py install         # Interactive installation
  python3 deploy.py install --auto  # Unattended installation
  python3 deploy.py serve           # Start services
  python3 deploy.py stop            # Stop services
  python3 deploy.py status          # Show status
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Detect command
    subparsers.add_parser("detect", help="Detect and report system hardware")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install the AI server")
    install_parser.add_argument("--auto", action="store_true", help="Unattended installation with defaults")
    
    # Serve command
    subparsers.add_parser("serve", help="Start all services")
    subparsers.add_parser("start", help="Start all services (alias for serve)")
    
    # Stop command
    subparsers.add_parser("stop", help="Stop all services")
    
    # Status command
    subparsers.add_parser("status", help="Show service status")
    
    args = parser.parse_args()
    
    if args.command == "detect":
        info = detect_system()
        print_system_report(info)
        
        # Save report
        report_file = Path.home() / "hardware_report.json"
        with open(report_file, 'w') as f:
            # Convert dataclasses to dicts
            report = asdict(info)
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {report_file}")
    
    elif args.command == "install":
        installer = Installer(auto_mode=args.auto)
        success = installer.run_full_install()
        sys.exit(0 if success else 1)
    
    elif args.command in ("serve", "start"):
        if not BASE_DIR.exists():
            print("❌ Not installed. Run 'python3 deploy.py install' first.")
            sys.exit(1)
        start_services()
    
    elif args.command == "stop":
        if not BASE_DIR.exists():
            print("❌ Not installed.")
            sys.exit(1)
        stop_services()
    
    elif args.command == "status":
        if not BASE_DIR.exists():
            print("❌ Not installed.")
            sys.exit(1)
        show_status()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
