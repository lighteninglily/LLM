#!/usr/bin/env python3
"""
Example: Using Web-Facing AI Server for Data Analysis

This script demonstrates how to interact with your web-facing
Qwen AI server for automated data analysis tasks.
"""

import requests
import pandas as pd
import json
from typing import Dict, Any

class AIDataAnalyzer:
    """Client for AI-powered data analysis"""
    
    def __init__(self, base_url: str, api_key: str = None):
        """
        Initialize the analyzer
        
        Args:
            base_url: Your domain (e.g., https://ai.yourdomain.com)
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_endpoint = f"{self.base_url}/api/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def analyze_dataset(self, data: pd.DataFrame, question: str, 
                       temperature: float = 0.3) -> Dict[str, Any]:
        """
        Analyze a pandas DataFrame using AI
        
        Args:
            data: Pandas DataFrame to analyze
            question: Analysis question
            temperature: Model temperature (0-1, lower = more focused)
        
        Returns:
            Dictionary with analysis results
        """
        # Convert DataFrame to CSV string for context
        csv_data = data.to_csv(index=False)
        
        # Truncate if too large (keep first 100 rows)
        if len(data) > 100:
            csv_data = data.head(100).to_csv(index=False)
            csv_data += f"\n... (showing first 100 of {len(data)} rows)"
        
        prompt = f"""You are a data analyst. Analyze the following dataset and answer the question.

Dataset:
```csv
{csv_data}
```

Question: {question}

Provide a detailed analysis with:
1. Key findings
2. Statistical insights
3. Trends or patterns
4. Actionable recommendations
"""
        
        payload = {
            "model": "Qwen/Qwen3-32B-Instruct",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert data analyst with strong statistical knowledge."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                headers=self.headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                "status": "success",
                "analysis": result["choices"][0]["message"]["content"],
                "model": result["model"],
                "usage": result.get("usage", {})
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def generate_python_code(self, task: str) -> str:
        """
        Generate Python code for data analysis tasks
        
        Args:
            task: Description of what code to generate
        
        Returns:
            Generated Python code
        """
        prompt = f"""Generate Python code using pandas and matplotlib for the following task:

Task: {task}

Provide clean, well-commented code that can be run directly.
"""
        
        payload = {
            "model": "Qwen/Qwen3-32B-Instruct",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a Python expert specializing in data analysis with pandas, numpy, and matplotlib."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,
            "max_tokens": 1500
        }
        
        response = requests.post(
            self.api_endpoint,
            headers=self.headers,
            json=payload,
            timeout=60
        )
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def summarize_report(self, report_text: str, max_length: int = 500) -> str:
        """
        Summarize a long report or document
        
        Args:
            report_text: Full text to summarize
            max_length: Maximum words in summary
        
        Returns:
            Summary text
        """
        prompt = f"""Summarize the following report in {max_length} words or less. Focus on key findings and actionable insights.

Report:
{report_text}
"""
        
        payload = {
            "model": "Qwen/Qwen3-32B-Instruct",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": max_length * 2
        }
        
        response = requests.post(
            self.api_endpoint,
            headers=self.headers,
            json=payload,
            timeout=60
        )
        
        result = response.json()
        return result["choices"][0]["message"]["content"]


# Example Usage
if __name__ == "__main__":
    
    # Initialize analyzer with your domain
    analyzer = AIDataAnalyzer(
        base_url="https://ai.yourdomain.com",  # Replace with your actual domain
        api_key=None  # Add API key if required
    )
    
    # Example 1: Analyze sales data
    print("Example 1: Sales Data Analysis")
    print("-" * 50)
    
    sales_data = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Revenue': [45000, 52000, 48000, 61000, 58000, 67000],
        'Customers': [150, 175, 160, 210, 195, 230],
        'Region': ['North', 'North', 'South', 'North', 'South', 'South']
    })
    
    result = analyzer.analyze_dataset(
        sales_data,
        "What are the key trends in revenue and customer growth? Which region is performing better?"
    )
    
    if result["status"] == "success":
        print(result["analysis"])
        print(f"\nTokens used: {result['usage']}")
    else:
        print(f"Error: {result['error']}")
    
    # Example 2: Generate analysis code
    print("\n\nExample 2: Generate Data Analysis Code")
    print("-" * 50)
    
    code = analyzer.generate_python_code(
        "Read a CSV file called 'sales.csv', calculate monthly growth rates, "
        "and create a bar chart showing revenue by month"
    )
    
    print(code)
    
    # Example 3: Summarize a report
    print("\n\nExample 3: Report Summarization")
    print("-" * 50)
    
    long_report = """
    Q2 2026 Performance Report
    
    Our analysis of Q2 2026 shows strong growth across all key metrics.
    Revenue increased by 23% compared to Q1, reaching $2.4M. Customer
    acquisition improved by 31%, with 1,250 new customers onboarded.
    
    The North region led growth with 45% increase, while South and East
    regions showed 18% and 22% growth respectively. Product line A 
    contributed 60% of total revenue, maintaining its position as our
    flagship offering.
    
    Challenges included a 15% increase in customer support tickets,
    primarily related to new feature adoption. We've allocated resources
    to improve onboarding documentation and training materials.
    
    Looking ahead to Q3, we project continued growth with emphasis on
    expanding into the West region and launching Product line B.
    """
    
    summary = analyzer.summarize_report(long_report, max_length=100)
    print(summary)
    
    # Example 4: Batch analysis
    print("\n\nExample 4: Batch Analysis of Multiple Datasets")
    print("-" * 50)
    
    datasets = {
        "Product A": pd.DataFrame({
            'Quarter': ['Q1', 'Q2', 'Q3', 'Q4'],
            'Sales': [100000, 120000, 135000, 150000]
        }),
        "Product B": pd.DataFrame({
            'Quarter': ['Q1', 'Q2', 'Q3', 'Q4'],
            'Sales': [80000, 85000, 90000, 95000]
        })
    }
    
    for product, data in datasets.items():
        result = analyzer.analyze_dataset(
            data,
            f"Analyze the sales trend for {product}. Is it growing?"
        )
        print(f"\n{product}:")
        if result["status"] == "success":
            print(result["analysis"][:200] + "...")  # Truncate for example
