#!/usr/bin/env python3
"""
AI Data Analyst with Code Execution

This creates a "Code Interpreter" style experience where the AI can:
1. Read your uploaded data files
2. Write Python code to analyze them
3. Execute the code and return results
4. Generate visualizations

Usage:
    python3 ai-data-analyst.py --file sales_data.csv "What are the trends?"
    python3 ai-data-analyst.py --folder ./data "Compare all datasets"
"""

import os
import sys
import json
import argparse
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import requests

class AIDataAnalyst:
    """AI-powered data analyst with code execution"""
    
    def __init__(self, llm_url: str = "http://localhost:8000/v1", 
                 model: str = "Qwen/Qwen3-32B-Instruct"):
        self.llm_url = llm_url
        self.model = model
        self.work_dir = Path(tempfile.mkdtemp(prefix="ai_analyst_"))
        self.conversation_history = []
        
    def _call_llm(self, messages: list, temperature: float = 0.2) -> str:
        """Call the local LLM"""
        response = requests.post(
            f"{self.llm_url}/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 4000
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def _execute_python(self, code: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute Python code safely and return results"""
        # Create a script file
        script_path = self.work_dir / "analysis_script.py"
        
        # Wrap code to capture output and save figures
        wrapped_code = f'''
import sys
import warnings
warnings.filterwarnings('ignore')

# Set up matplotlib for headless operation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Change to work directory
import os
os.chdir("{self.work_dir}")

# Execute user code
try:
{self._indent_code(code, 4)}
    
    # Save any open figures
    for i, fig_num in enumerate(plt.get_fignums()):
        plt.figure(fig_num)
        plt.savefig(f"figure_{{i}}.png", dpi=150, bbox_inches='tight')
        print(f"[Saved figure_{{i}}.png]")
    
except Exception as e:
    print(f"Error: {{type(e).__name__}}: {{e}}", file=sys.stderr)
    sys.exit(1)
'''
        
        with open(script_path, 'w') as f:
            f.write(wrapped_code)
        
        # Execute
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.work_dir)
            )
            
            # Collect generated figures
            figures = list(self.work_dir.glob("figure_*.png"))
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "figures": [str(f) for f in figures]
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds",
                "figures": []
            }
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code block"""
        indent = " " * spaces
        return "\n".join(indent + line for line in code.split("\n"))
    
    def _extract_code(self, response: str) -> Optional[str]:
        """Extract Python code from LLM response"""
        # Look for ```python blocks
        if "```python" in response:
            start = response.find("```python") + 9
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()
        
        # Look for ``` blocks
        if "```" in response:
            start = response.find("```") + 3
            # Skip language identifier if present
            if response[start:start+10].split('\n')[0].strip() in ['python', 'py', '']:
                start = response.find('\n', start) + 1
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()
        
        return None
    
    def analyze(self, query: str, data_files: list[Path]) -> str:
        """
        Analyze data files based on user query
        
        Args:
            query: User's analysis question
            data_files: List of data file paths
            
        Returns:
            Analysis results with any generated visualizations
        """
        # Copy data files to work directory
        for f in data_files:
            if f.exists():
                import shutil
                shutil.copy(f, self.work_dir / f.name)
        
        # Build file context
        file_info = []
        for f in data_files:
            dest = self.work_dir / f.name
            if dest.suffix.lower() == '.csv':
                # Preview CSV
                try:
                    import pandas as pd
                    df = pd.read_csv(dest, nrows=5)
                    file_info.append(f"""
File: {f.name}
Columns: {list(df.columns)}
Shape: {pd.read_csv(dest).shape}
Preview:
{df.to_string()}
""")
                except Exception as e:
                    file_info.append(f"File: {f.name} (Error reading: {e})")
            else:
                file_info.append(f"File: {f.name} ({f.suffix})")
        
        # System prompt for code generation
        system_prompt = f"""You are an expert data analyst. You have access to the following data files in the current directory:

{chr(10).join(file_info)}

Your task is to analyze this data and answer the user's question.

IMPORTANT RULES:
1. ALWAYS write Python code to perform analysis
2. Use pandas for data manipulation
3. Use matplotlib or seaborn for visualizations
4. Print your findings clearly
5. Create visualizations when they help explain results
6. Handle missing data appropriately
7. Be precise with numbers and statistics

Respond with:
1. Your analysis approach (brief)
2. Python code in a ```python block
3. Interpretation of expected results

The code will be executed and results returned to you."""

        # First pass: generate analysis code
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = self._call_llm(messages)
        code = self._extract_code(response)
        
        if not code:
            return f"I couldn't generate analysis code. Here's my response:\n\n{response}"
        
        # Execute the code
        print(f"\n{'='*60}")
        print("Executing analysis code...")
        print('='*60)
        print(code)
        print('='*60 + "\n")
        
        result = self._execute_python(code)
        
        if not result["success"]:
            # Try to fix the code
            fix_messages = messages + [
                {"role": "assistant", "content": response},
                {"role": "user", "content": f"""The code produced an error:

{result['stderr']}

Please fix the code and try again. Remember the files are in the current directory."""}
            ]
            
            response = self._call_llm(fix_messages)
            code = self._extract_code(response)
            
            if code:
                result = self._execute_python(code)
        
        # Build final response
        output = []
        
        if result["stdout"]:
            output.append("**Analysis Results:**\n")
            output.append(result["stdout"])
        
        if result["stderr"] and not result["success"]:
            output.append("\n**Errors:**\n")
            output.append(result["stderr"])
        
        if result["figures"]:
            output.append(f"\n**Generated {len(result['figures'])} visualization(s):**")
            for fig in result["figures"]:
                output.append(f"  - {fig}")
        
        # Get LLM interpretation of results
        if result["success"] and result["stdout"]:
            interpret_messages = messages + [
                {"role": "assistant", "content": response},
                {"role": "user", "content": f"""The code executed successfully. Here are the results:

{result['stdout']}

Please provide a clear, executive-summary interpretation of these findings. Focus on:
1. Key insights
2. Notable patterns or anomalies
3. Actionable recommendations

Be concise and business-focused."""}
            ]
            
            interpretation = self._call_llm(interpret_messages, temperature=0.3)
            output.append("\n**Interpretation:**\n")
            output.append(interpretation)
        
        return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="AI Data Analyst with Code Execution"
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        help="Analysis question"
    )
    
    parser.add_argument(
        "--file", "-f",
        action="append",
        dest="files",
        help="Data file to analyze (can specify multiple)"
    )
    
    parser.add_argument(
        "--folder",
        help="Folder containing data files"
    )
    
    parser.add_argument(
        "--llm-url",
        default="http://localhost:8000/v1",
        help="LLM API URL"
    )
    
    parser.add_argument(
        "--model",
        default="Qwen/Qwen3-32B-Instruct",
        help="Model name"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode"
    )
    
    args = parser.parse_args()
    
    # Collect files
    files = []
    
    if args.files:
        files.extend([Path(f) for f in args.files])
    
    if args.folder:
        folder = Path(args.folder)
        files.extend(folder.glob("*.csv"))
        files.extend(folder.glob("*.xlsx"))
        files.extend(folder.glob("*.json"))
    
    if not files:
        print("No data files specified. Use --file or --folder")
        sys.exit(1)
    
    print(f"Loaded {len(files)} file(s):")
    for f in files:
        print(f"  - {f}")
    
    analyst = AIDataAnalyst(args.llm_url, args.model)
    
    if args.interactive:
        print("\nInteractive mode. Type 'quit' to exit.\n")
        while True:
            try:
                query = input("\nYour question: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                if not query:
                    continue
                
                result = analyst.analyze(query, files)
                print("\n" + result)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    elif args.query:
        result = analyst.analyze(args.query, files)
        print(result)
    
    else:
        print("Provide a query or use --interactive mode")
        sys.exit(1)


if __name__ == "__main__":
    main()
