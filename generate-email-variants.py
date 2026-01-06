#!/usr/bin/env python3
"""
Generate A/B test variants for email campaigns

Creates multiple subject line and preview text variants optimized for different hypotheses.

Usage:
    python3 generate-email-variants.py --subject "Your subject" --preview "Preview text"
    python3 generate-email-variants.py --subject "Sale this weekend" --variants 5
"""

import requests
import json
import argparse
import sys

class EmailVariantGenerator:
    """Generate A/B test variants using LLM"""
    
    def __init__(self, workspace: str = "Email Marketing Optimizer", base_url: str = "http://localhost:3001"):
        self.workspace = workspace
        self.base_url = base_url.rstrip('/')
        self.workspace_slug = workspace.lower().replace(" ", "-")
        self.api_url = f"{self.base_url}/api/workspace/{self.workspace_slug}/chat"
    
    def query_llm(self, prompt: str) -> str:
        """Send query to LLM workspace"""
        try:
            response = requests.post(
                self.api_url,
                json={"message": prompt},
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("textResponse", "")
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error querying LLM: {e}"
    
    def generate_variants(self, subject: str, preview: str = "", num_variants: int = 3, 
                         target_audience: str = "", campaign_goal: str = "") -> str:
        """Generate A/B test variants"""
        
        context = ""
        if target_audience:
            context += f"\n**Target Audience:** {target_audience}"
        if campaign_goal:
            context += f"\n**Campaign Goal:** {campaign_goal}"
        
        prompt = f"""
Generate {num_variants} A/B test variants for this email campaign:

**Original:**
Subject: {subject}
Preview: {preview if preview else "N/A"}{context}

**Requirements:**
1. Each variant should test a DIFFERENT hypothesis (e.g., personalization, urgency, curiosity, social proof, value proposition)
2. Follow email marketing best practices from the knowledge base
3. Optimize for mobile (40 characters max for subject line preferred)
4. Include expected performance prediction based on historical data
5. Explain the specific rationale for each variant

**Output Format:**
For each variant, provide:
- Variant name and hypothesis being tested
- Subject line
- Preview text
- Expected lift percentage vs original
- Detailed rationale citing best practices

Make variants distinctly different to provide meaningful test results.
"""
        
        return self.query_llm(prompt)
    
    def optimize_existing(self, subject: str, preview: str = "", 
                         current_open_rate: float = 0, current_click_rate: float = 0) -> str:
        """Optimize an existing campaign based on performance"""
        
        performance_context = ""
        if current_open_rate > 0:
            performance_context = f"""
**Current Performance:**
- Open Rate: {current_open_rate:.1f}%
- Click Rate: {current_click_rate:.1f}%
"""
        
        prompt = f"""
Optimize this underperforming email campaign:

**Current Version:**
Subject: {subject}
Preview: {preview if preview else "N/A"}
{performance_context}

**Task:**
1. Identify specific problems with the current subject and preview
2. Compare against best practices and high-performing campaigns in the database
3. Generate 3 improved versions that address the identified issues
4. Predict expected performance improvement for each

Be specific about what's wrong and how each improvement fixes it.
"""
        
        return self.query_llm(prompt)
    
    def generate_for_audience(self, campaign_type: str, audience: str, key_message: str) -> str:
        """Generate campaign variants for specific audience"""
        
        prompt = f"""
Create email campaign variants for:

**Campaign Type:** {campaign_type}
**Target Audience:** {audience}
**Key Message:** {key_message}

**Generate 3 variants:**
1. One optimized for highest open rate
2. One optimized for highest click-through
3. One balanced for both metrics

For each variant provide:
- Subject line
- Preview text
- Rationale based on audience characteristics
- Expected performance

Use best practices and audience insights from the knowledge base.
"""
        
        return self.query_llm(prompt)


def main():
    parser = argparse.ArgumentParser(
        description="Generate A/B test variants for email campaigns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 3 variants
  python3 generate-email-variants.py --subject "Weekend Sale" --preview "Save big"
  
  # Generate 5 variants with context
  python3 generate-email-variants.py \\
    --subject "Your weekly newsletter" \\
    --preview "What's new" \\
    --variants 5 \\
    --audience "Active subscribers" \\
    --goal "Increase engagement"
  
  # Optimize underperforming campaign
  python3 generate-email-variants.py \\
    --subject "Monthly update" \\
    --optimize \\
    --open-rate 12.5 \\
    --click-rate 1.8
        """
    )
    
    parser.add_argument(
        "--subject",
        required=True,
        help="Original subject line"
    )
    
    parser.add_argument(
        "--preview",
        default="",
        help="Original preview text (optional)"
    )
    
    parser.add_argument(
        "--variants",
        type=int,
        default=3,
        help="Number of variants to generate (default: 3)"
    )
    
    parser.add_argument(
        "--audience",
        default="",
        help="Target audience description (optional)"
    )
    
    parser.add_argument(
        "--goal",
        default="",
        help="Campaign goal (optional)"
    )
    
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Optimize existing campaign instead of generating variants"
    )
    
    parser.add_argument(
        "--open-rate",
        type=float,
        default=0,
        help="Current open rate (for optimization mode)"
    )
    
    parser.add_argument(
        "--click-rate",
        type=float,
        default=0,
        help="Current click rate (for optimization mode)"
    )
    
    parser.add_argument(
        "--workspace",
        default="Email Marketing Optimizer",
        help="Workspace name (default: Email Marketing Optimizer)"
    )
    
    parser.add_argument(
        "--url",
        default="http://localhost:3001",
        help="AnythingLLM server URL (default: http://localhost:3001)"
    )
    
    parser.add_argument(
        "--output",
        help="Save output to file (optional)"
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = EmailVariantGenerator(workspace=args.workspace, base_url=args.url)
    
    print("\n" + "="*60)
    if args.optimize:
        print("OPTIMIZING CAMPAIGN")
    else:
        print(f"GENERATING {args.variants} A/B TEST VARIANTS")
    print("="*60 + "\n")
    
    print(f"Original Subject: {args.subject}")
    if args.preview:
        print(f"Original Preview: {args.preview}")
    print("\nGenerating...\n")
    
    # Generate variants or optimization
    if args.optimize:
        result = generator.optimize_existing(
            args.subject, 
            args.preview,
            args.open_rate,
            args.click_rate
        )
    else:
        result = generator.generate_variants(
            args.subject,
            args.preview,
            args.variants,
            args.audience,
            args.goal
        )
    
    # Output results
    print(result)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(f"# Email Variant Generation\n\n")
            f.write(f"**Original Subject:** {args.subject}\n")
            if args.preview:
                f.write(f"**Original Preview:** {args.preview}\n")
            f.write(f"\n---\n\n")
            f.write(result)
        
        print(f"\n\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
