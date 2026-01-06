#!/usr/bin/env python3
"""
Automated Email Campaign Analyzer

Runs analysis on email campaign data and generates improvement recommendations.

Usage:
    python3 analyze-email-campaigns.py --data campaigns.csv --output report.md
    python3 analyze-email-campaigns.py --data campaigns.csv --weekly-insights
"""

import pandas as pd
import requests
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, Optional

class EmailCampaignAnalyzer:
    """Analyze email campaigns using LLM workspace"""
    
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
    
    def analyze_campaign(self, campaign_data: pd.Series) -> str:
        """Analyze a single campaign"""
        prompt = f"""
Analyze this email campaign:

**Campaign Details:**
Subject: {campaign_data['subject_line']}
Preview: {campaign_data.get('preview_text', 'N/A')}
Sent: {campaign_data['send_date']}
Recipients: {int(campaign_data['recipients']):,}
Opens: {int(campaign_data['opens']):,} ({campaign_data['open_rate']:.1f}%)
Clicks: {int(campaign_data['clicks']):,} ({campaign_data['click_rate']:.1f}%)
Conversions: {int(campaign_data.get('conversions', 0)):,} ({campaign_data.get('conversion_rate', 0):.2f}%)

**Tasks:**
1. Rate performance vs industry benchmarks (use best practices data)
2. Identify what worked well and what didn't
3. Provide 3 specific, actionable improvements
4. Generate 2 improved subject line variants for A/B testing

Be specific and cite best practices from the knowledge base.
"""
        
        return self.query_llm(prompt)
    
    def batch_analysis(self, campaigns_df: pd.DataFrame) -> str:
        """Analyze all campaigns and generate report"""
        report = []
        report.append("# Email Campaign Analysis Report")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"**Total Campaigns:** {len(campaigns_df)}\n")
        
        # Overall statistics
        report.append("## Overall Performance\n")
        report.append(f"- **Average Open Rate:** {campaigns_df['open_rate'].mean():.1f}%")
        report.append(f"- **Average Click Rate:** {campaigns_df['click_rate'].mean():.1f}%")
        
        if 'conversion_rate' in campaigns_df.columns:
            report.append(f"- **Average Conversion:** {campaigns_df['conversion_rate'].mean():.2f}%")
        
        report.append("")
        
        # Top performers
        top_3 = campaigns_df.nlargest(3, 'open_rate')
        report.append("## Top 3 Performers\n")
        for idx, campaign in top_3.iterrows():
            report.append(f"- **{campaign['subject_line']}** - {campaign['open_rate']:.1f}% open rate")
        report.append("")
        
        # Bottom performers needing improvement
        bottom_3 = campaigns_df.nsmallest(3, 'open_rate')
        report.append("## Bottom 3 Performers (Need Improvement)\n")
        for idx, campaign in bottom_3.iterrows():
            report.append(f"- **{campaign['subject_line']}** - {campaign['open_rate']:.1f}% open rate")
        report.append("")
        
        # Analyze low performers
        median_open = campaigns_df['open_rate'].median()
        low_performers = campaigns_df[campaigns_df['open_rate'] < median_open]
        
        report.append("## Detailed Analysis: Campaigns Below Median Performance\n")
        
        for idx, campaign in low_performers.iterrows():
            report.append(f"### Campaign: {campaign['subject_line']}\n")
            
            print(f"Analyzing: {campaign['subject_line']}...")
            analysis = self.analyze_campaign(campaign)
            report.append(analysis)
            report.append("\n---\n")
        
        return "\n".join(report)
    
    def generate_weekly_insights(self, campaigns_df: pd.DataFrame) -> str:
        """Generate strategic weekly insights"""
        
        # Prepare summary stats for context
        stats = f"""
Total campaigns analyzed: {len(campaigns_df)}
Average open rate: {campaigns_df['open_rate'].mean():.1f}%
Average click rate: {campaigns_df['click_rate'].mean():.1f}%
Top performer: {campaigns_df.loc[campaigns_df['open_rate'].idxmax(), 'subject_line']} ({campaigns_df['open_rate'].max():.1f}%)
Bottom performer: {campaigns_df.loc[campaigns_df['open_rate'].idxmin(), 'subject_line']} ({campaigns_df['open_rate'].min():.1f}%)
"""
        
        prompt = f"""
Based on all email campaigns in the database and this week's performance:

{stats}

**Please provide:**

1. **Pattern Analysis:** What are the 3 most important patterns that separate high performers from low performers in our campaigns? Use specific examples from the data.

2. **Action Plan:** Create a prioritized action plan for improving next week's campaigns. Be specific and actionable.

3. **Template Framework:** Generate a proven subject line template structure that incorporates our best practices and successful patterns.

4. **A/B Test Strategy:** Recommend 2-3 specific hypotheses we should test in upcoming campaigns.

Use data from campaigns and best practices from the knowledge base. Be specific with numbers and examples.
"""
        
        print("Generating weekly insights...")
        return self.query_llm(prompt)
    
    def compare_campaigns(self, campaign_id_1: str, campaign_id_2: str, campaigns_df: pd.DataFrame) -> str:
        """Compare two campaigns head-to-head"""
        
        camp1 = campaigns_df[campaigns_df['campaign_id'] == campaign_id_1].iloc[0]
        camp2 = campaigns_df[campaigns_df['campaign_id'] == campaign_id_2].iloc[0]
        
        prompt = f"""
Compare these two campaigns and explain the performance difference:

**Campaign A:**
Subject: {camp1['subject_line']}
Open Rate: {camp1['open_rate']:.1f}%
Click Rate: {camp1['click_rate']:.1f}%

**Campaign B:**
Subject: {camp2['subject_line']}
Open Rate: {camp2['open_rate']:.1f}%
Click Rate: {camp2['click_rate']:.1f}%

**Analysis Required:**
1. What specifically caused the performance difference?
2. Which best practices did the better campaign follow?
3. What can we learn and apply to future campaigns?
"""
        
        return self.query_llm(prompt)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze email campaigns using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--data",
        required=True,
        help="CSV file with campaign data"
    )
    
    parser.add_argument(
        "--output",
        default="campaign-analysis.md",
        help="Output report file (default: campaign-analysis.md)"
    )
    
    parser.add_argument(
        "--weekly-insights",
        action="store_true",
        help="Generate weekly strategic insights instead of detailed analysis"
    )
    
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=('CAMPAIGN_ID_1', 'CAMPAIGN_ID_2'),
        help="Compare two campaigns by ID"
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
    
    args = parser.parse_args()
    
    # Load campaign data
    print(f"Loading campaign data from: {args.data}")
    try:
        campaigns = pd.read_csv(args.data)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        sys.exit(1)
    
    # Validate required columns
    required_cols = ['subject_line', 'send_date', 'recipients', 'opens', 'clicks']
    missing_cols = [col for col in required_cols if col not in campaigns.columns]
    
    if missing_cols:
        print(f"Error: Missing required columns: {', '.join(missing_cols)}")
        print(f"Available columns: {', '.join(campaigns.columns)}")
        sys.exit(1)
    
    # Calculate rates if not present
    if 'open_rate' not in campaigns.columns:
        campaigns['open_rate'] = (campaigns['opens'] / campaigns['recipients']) * 100
    
    if 'click_rate' not in campaigns.columns:
        campaigns['click_rate'] = (campaigns['clicks'] / campaigns['recipients']) * 100
    
    if 'conversions' in campaigns.columns and 'conversion_rate' not in campaigns.columns:
        campaigns['conversion_rate'] = (campaigns['conversions'] / campaigns['recipients']) * 100
    
    print(f"Loaded {len(campaigns)} campaigns")
    print()
    
    # Initialize analyzer
    analyzer = EmailCampaignAnalyzer(workspace=args.workspace, base_url=args.url)
    
    # Run analysis based on mode
    if args.compare:
        # Compare two campaigns
        result = analyzer.compare_campaigns(args.compare[0], args.compare[1], campaigns)
        print(result)
    
    elif args.weekly_insights:
        # Generate weekly insights
        insights = analyzer.generate_weekly_insights(campaigns)
        print("\n" + "="*60)
        print("WEEKLY INSIGHTS")
        print("="*60 + "\n")
        print(insights)
        
        # Optionally save to file
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(f"# Weekly Email Marketing Insights\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                f.write(insights)
            print(f"\nInsights saved to: {args.output}")
    
    else:
        # Full batch analysis
        print("Running detailed campaign analysis...")
        print("This may take a few minutes...\n")
        
        report = analyzer.batch_analysis(campaigns)
        
        # Save report
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n{'='*60}")
        print(f"Analysis complete!")
        print(f"Report saved to: {args.output}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
