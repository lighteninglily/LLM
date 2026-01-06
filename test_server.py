#!/usr/bin/env python3
"""
Test script to verify the Local AI Server is working correctly.

Usage:
    python3 test_server.py
"""

import urllib.request
import urllib.error
import json
import sys
import time
from pathlib import Path

VLLM_URL = "http://localhost:8000"
ANYTHINGLLM_URL = "http://localhost:3001"


def get_api_key():
    """Retrieve vLLM API key from .env file."""
    try:
        env_path = Path.home() / ".local-ai-server" / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("VLLM_API_KEY="):
                        return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return "not-needed"


def test_vllm_health():
    """Test vLLM health endpoint."""
    print("Testing vLLM health...", end=" ")
    try:
        headers = {"Authorization": f"Bearer {get_api_key()}"}
        req = urllib.request.Request(f"{VLLM_URL}/health", headers=headers)
        response = urllib.request.urlopen(req, timeout=10)
        if response.status == 200:
            print("✅ OK")
            return True
    except urllib.error.URLError as e:
        print(f"❌ Failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False


def test_vllm_models():
    """Test vLLM models endpoint."""
    print("Testing vLLM models list...", end=" ")
    try:
        headers = {"Authorization": f"Bearer {get_api_key()}"}
        req = urllib.request.Request(f"{VLLM_URL}/v1/models", headers=headers)
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read())
        models = [m['id'] for m in data.get('data', [])]
        if models:
            print(f"✅ OK - Model: {models[0]}")
            return True
        else:
            print("❌ No models loaded")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False


def test_vllm_completion():
    """Test vLLM chat completion."""
    print("Testing vLLM chat completion...", end=" ")
    
    payload = {
        "model": "default",  # vLLM will use the loaded model
        "messages": [
            {"role": "user", "content": "Say 'hello' and nothing else."}
        ],
        "max_tokens": 10,
        "temperature": 0
    }
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_api_key()}"
        }
        req = urllib.request.Request(
            f"{VLLM_URL}/v1/chat/completions",
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method="POST"
        )
        response = urllib.request.urlopen(req, timeout=60)
        data = json.loads(response.read())
        
        if 'choices' in data and len(data['choices']) > 0:
            content = data['choices'][0]['message']['content']
            print(f"✅ OK - Response: '{content[:50]}...'")
            return True
        else:
            print("❌ Invalid response format")
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False


def test_anythingllm_health():
    """Test AnythingLLM health endpoint."""
    print("Testing AnythingLLM health...", end=" ")
    try:
        response = urllib.request.urlopen(f"{ANYTHINGLLM_URL}/api/ping", timeout=10)
        if response.status == 200:
            print("✅ OK")
            return True
    except urllib.error.URLError as e:
        print(f"❌ Failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False


def test_anythingllm_ui():
    """Test AnythingLLM web UI is accessible."""
    print("Testing AnythingLLM UI...", end=" ")
    try:
        response = urllib.request.urlopen(ANYTHINGLLM_URL, timeout=10)
        if response.status == 200:
            print("✅ OK")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
    return False


def main():
    print("=" * 60)
    print("LOCAL AI SERVER - SYSTEM TEST")
    print("=" * 60)
    print()
    
    results = {
        "vLLM Health": test_vllm_health(),
        "vLLM Models": test_vllm_models(),
        "vLLM Completion": test_vllm_completion(),
        "AnythingLLM Health": test_anythingllm_health(),
        "AnythingLLM UI": test_anythingllm_ui(),
    }
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print()
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print()
        print("🎉 All tests passed! Your server is ready.")
        print()
        print("Access points:")
        print(f"  - AnythingLLM UI: {ANYTHINGLLM_URL}")
        print(f"  - vLLM API: {VLLM_URL}/v1")
        return 0
    else:
        print()
        print("⚠️  Some tests failed. Check the logs:")
        print("  docker compose logs vllm")
        print("  docker compose logs anythingllm")
        return 1


if __name__ == "__main__":
    sys.exit(main())
