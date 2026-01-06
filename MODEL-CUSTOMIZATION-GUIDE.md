# Model Customization Guide - Making It Yours

## Customization Levels (Easy → Advanced)

```
Level 1: System Prompts ─────────────────────── ✓ EASIEST (5 minutes)
   └─▶ Change how AI responds without retraining

Level 2: Workspace Settings ─────────────────── ✓ EASY (10 minutes)
   └─▶ Different behavior per workspace

Level 3: Few-Shot Examples ──────────────────── ◉ MEDIUM (30 minutes)
   └─▶ Show AI examples of desired output

Level 4: Prompt Templates ───────────────────── ◉ MEDIUM (1 hour)
   └─▶ Pre-built queries for common tasks

Level 5: Fine-Tuning ────────────────────────── ✗ ADVANCED (days)
   └─▶ Retrain model on your data (usually not needed)
```

---

## Level 1: System Prompts (RECOMMENDED START)

### What It Does
Changes how the AI behaves globally without any training.

### How to Do It

**Edit AnythingLLM System Prompt:**

1. Open AnythingLLM UI: http://localhost:3001
2. Go to Workspace Settings
3. Find "System Prompt" section
4. Replace default with custom instructions

### Example System Prompts

#### For Financial Analysis
```
You are a financial analyst AI specialized in business data analysis.

Guidelines:
- Always show numbers with proper formatting ($50,000, not 50000)
- Calculate totals, averages, and percentages automatically
- Highlight trends and anomalies
- Use tables for comparisons
- Cite source files for all numbers

When analyzing spreadsheets:
1. Summarize key metrics first
2. Show detailed breakdown
3. Provide actionable insights

Be concise but thorough. Assume user has business context.
```

#### For Customer Support
```
You are a helpful customer support AI assistant.

Guidelines:
- Be friendly and empathetic
- Provide step-by-step solutions
- Always cite relevant policy documents
- If unsure, say "Let me check our documentation"
- Offer to escalate complex issues

Response format:
1. Acknowledge the question
2. Provide clear answer
3. Offer additional help

Use simple language. Avoid jargon unless necessary.
```

#### For Technical Documentation
```
You are a technical documentation AI for software developers.

Guidelines:
- Be precise and accurate
- Include code examples when relevant
- Explain "why" not just "how"
- Cite specific files and line numbers
- Link related documentation

When explaining code:
1. High-level overview first
2. Detailed explanation
3. Common pitfalls
4. Best practices

Use technical language. Assume developer audience.
```

#### For Data Science Analysis
```
You are a data science AI assistant.

Guidelines:
- Provide statistical analysis
- Suggest visualizations
- Explain methodology
- Note data quality issues
- Recommend next steps

Analysis format:
1. Data overview (rows, columns, types)
2. Descriptive statistics
3. Key findings
4. Recommendations

Always validate assumptions. Flag missing data.
```

---

## Level 2: Workspace-Specific Behavior

### Different Prompts Per Workspace

Each workspace can have unique system prompt:

**Workspace: "Sales Analysis"**
```
System Prompt: Focus on revenue, growth rates, and sales trends.
Always compare to previous periods. Highlight top performers.
```

**Workspace: "HR Policies"**
```
System Prompt: Be formal and precise. Always cite policy section.
If policy unclear, say so and recommend contacting HR directly.
```

**Workspace: "Technical Docs"**
```
System Prompt: Provide code examples. Explain technical concepts.
Link to related documentation. Use developer terminology.
```

### Temperature Settings Per Workspace

Control creativity vs. consistency:

- **Financial/Legal (0.1-0.3)**: Very consistent, factual
- **General Q&A (0.5-0.7)**: Balanced
- **Creative/Brainstorming (0.8-1.0)**: More varied responses

**How to Set:**
1. Workspace Settings
2. "OpenAI Temperature" slider
3. Lower = more consistent, Higher = more creative

### Context Length Per Workspace

Control how much document context to include:

- **Precise answers (2-4 chunks)**: When you want specific facts
- **Comprehensive answers (6-8 chunks)**: When you need full context
- **Maximum context (10+ chunks)**: For complex multi-document queries

**How to Set:**
1. Workspace Settings
2. "Top N Results" field
3. Higher = more context (but slower)

---

## Level 3: Few-Shot Examples

### What It Does
Show the AI examples of exactly how you want it to respond.

### How to Use

Include examples in your system prompt:

```
You are a sales report generator.

Example Input: "Summarize Q1 sales"
Example Output:
┌─────────────────────────────────┐
│ Q1 2024 SALES SUMMARY          │
├─────────────────────────────────┤
│ Total Revenue:    $1,250,000   │
│ Growth vs Q4:     +15%         │
│ Top Region:       North        │
│ Top Product:      Widget A     │
└─────────────────────────────────┘

Key Insights:
• North region exceeded targets by 20%
• Widget A drove 35% of total revenue
• March showed acceleration (+8% MoM)

Recommendation: Increase inventory for Widget A in North region.

---

Now respond to user queries in this format.
```

### More Examples

#### For Structured Data Output
```
When asked about customer data, always respond in this format:

Customer: Acme Corp
├─ Contact: john@acme.com
├─ Total Spent: $150,000
├─ Last Purchase: 2024-01-15
├─ Status: Active
└─ Notes: VIP customer, net-30 terms

Follow this structure for all customer queries.
```

#### For Code Generation
```
When generating Python code, use this format:

```python
# Purpose: [What the code does]
# Input: [Expected input]
# Output: [Expected output]

def function_name(params):
    """
    Detailed docstring explaining the function.
    """
    # Step 1: [Explanation]
    result = process(params)
    
    # Step 2: [Explanation]
    return result

# Example usage
example = function_name(test_data)
print(example)
```

Include error handling and comments.
```

---

## Level 4: Prompt Templates (Pre-Built Queries)

### Create Reusable Query Templates

Instead of users typing full questions, provide templates:

**Financial Analysis Templates:**
```
1. "Show me Q[X] revenue breakdown by [category/region/product]"
2. "Compare [period1] to [period2] for [metric]"
3. "What are the top 10 [customers/products] by [revenue/volume]?"
4. "Calculate growth rate for [category] over [timeframe]"
5. "Identify trends in [dataset] for last [X] months"
```

**Customer Support Templates:**
```
1. "What is our policy on [topic]?"
2. "How do I [action/process]?"
3. "Troubleshoot [issue/error]"
4. "Find documentation about [feature]"
5. "What are requirements for [process]?"
```

**Data Science Templates:**
```
1. "Analyze distribution of [column] in [dataset]"
2. "Find correlations between [var1] and [var2]"
3. "Detect outliers in [metric]"
4. "Summarize statistics for [dataset]"
5. "Suggest visualizations for [data_type]"
```

### Implementation

Create a simple HTML page with buttons:

```html
<!-- templates.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Query Templates</title>
    <style>
        button { margin: 10px; padding: 15px; font-size: 16px; }
    </style>
</head>
<body>
    <h1>Sales Analysis Templates</h1>
    
    <button onclick="query('Show Q4 revenue breakdown by region')">
        Q4 Revenue by Region
    </button>
    
    <button onclick="query('What are top 10 customers by revenue?')">
        Top 10 Customers
    </button>
    
    <button onclick="query('Calculate month-over-month growth')">
        Monthly Growth
    </button>
    
    <script>
        function query(text) {
            // Copy to clipboard or open AnythingLLM with pre-filled query
            navigator.clipboard.writeText(text);
            alert('Query copied! Paste in AI chat.');
        }
    </script>
</body>
</html>
```

---

## Level 5: Fine-Tuning (Advanced)

### When to Consider Fine-Tuning

**DON'T fine-tune if:**
- ✗ You just need different response style (use system prompts)
- ✗ You need domain knowledge (use RAG - already built in)
- ✗ You want specific output format (use few-shot examples)

**DO fine-tune if:**
- ✓ You need very specialized technical language
- ✓ You have 10,000+ examples of desired behavior
- ✓ System prompts aren't achieving the quality you need
- ✓ You're willing to invest significant time/resources

### Fine-Tuning Process (If Needed)

**Requirements:**
- Training data: 1,000-10,000 examples
- GPU: Can use your RTX 5090
- Time: Days to weeks
- Expertise: Machine learning knowledge

**Basic Steps:**

1. **Collect Training Data**
```json
[
  {
    "input": "What were Q1 sales?",
    "output": "Q1 2024 sales were $1.2M, up 15% from Q4..."
  },
  {
    "input": "Show top customers",
    "output": "Top 3 customers by revenue:\n1. Acme Corp..."
  }
]
```

2. **Prepare Dataset**
```bash
# Convert to training format
python3 prepare_dataset.py \
  --input training_data.json \
  --output train.jsonl
```

3. **Fine-Tune Model**
```bash
# Using LoRA (efficient fine-tuning)
python3 fine_tune.py \
  --base-model Qwen/Qwen3-32B-Instruct \
  --dataset train.jsonl \
  --output custom-model
```

4. **Update Configuration**
```bash
# Point to your fine-tuned model
nano ~/.local-ai-server/.env
LLM_MODEL=./custom-models/my-tuned-qwen
```

**Cost/Effort:**
- Time: 2-7 days for training + testing
- Complexity: High (ML expertise needed)
- Storage: +20-30GB for fine-tuned model

**Recommendation: Start with system prompts first. Only fine-tune if absolutely necessary.**

---

## Practical Customization Workflow

### For Your Use Case

**Step 1: Define Your Needs (15 minutes)**

Ask yourself:
- What type of questions will users ask?
- What tone should responses have? (Formal/casual/technical)
- What format should answers follow? (Bullet points/tables/prose)
- What domain knowledge is needed? (Already in RAG documents)

**Step 2: Write System Prompt (30 minutes)**

```
You are [role description].

Your purpose is to [primary function].

Guidelines:
- [Rule 1]
- [Rule 2]
- [Rule 3]

Response format:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Example response:
[Show exactly what you want]

Tone: [Professional/Casual/Technical]
```

**Step 3: Test and Iterate (1 hour)**

1. Set system prompt in workspace
2. Ask 10 test questions
3. Note what works / what doesn't
4. Adjust prompt
5. Test again

**Step 4: Create Templates (optional, 30 minutes)**

For common queries, create buttons or shortcuts.

**Step 5: Deploy (5 minutes)**

Share workspace with users, brief them on capabilities.

---

## Example Customizations by Industry

### Manufacturing Company

**System Prompt:**
```
You are a manufacturing data analyst AI.

Focus areas:
- Production efficiency metrics
- Quality control data
- Inventory levels
- Equipment utilization
- Supply chain status

Always:
- Show units of measure
- Highlight variances from targets
- Flag potential bottlenecks
- Calculate OEE (Overall Equipment Effectiveness)
- Suggest process improvements

Use manufacturing terminology. Assume operations team audience.
```

**Workspaces:**
- "Production Data" - Daily output, efficiency
- "Quality Control" - Defect rates, inspection results
- "Inventory" - Stock levels, reorder points

### Law Firm

**System Prompt:**
```
You are a legal research AI assistant.

Guidelines:
- Be extremely precise with citations
- Use formal legal language
- Always cite document names and page numbers
- Flag potential conflicts or ambiguities
- Distinguish between facts and interpretation

Format:
1. Direct answer to question
2. Supporting citations
3. Relevant precedents or policies
4. Caveats or limitations

Never provide legal advice. Recommend attorney review for complex matters.
```

**Workspaces:**
- "Case Files" - Client documents
- "Legal Research" - Case law, statutes
- "Templates" - Contract templates, forms

### Healthcare Organization

**System Prompt:**
```
You are a healthcare data analysis AI.

IMPORTANT: This is for administrative data only, not medical advice.

Focus areas:
- Patient volume and trends
- Operational efficiency
- Resource utilization
- Billing and insurance data
- Compliance documentation

Always:
- Maintain HIPAA awareness (no PHI in responses)
- Use proper medical terminology
- Show statistical confidence levels
- Flag data quality issues
- Cite source documents

For clinical questions, direct to medical staff.
```

---

## Quick Wins (Do These First)

### 1. Set Temperature (2 minutes)

**Financial/Legal workspaces: 0.2**
```
Workspace Settings → OpenAI Temperature → 0.2
```

**General workspaces: 0.5**
```
Workspace Settings → OpenAI Temperature → 0.5
```

### 2. Add Basic System Prompt (5 minutes)

```
You are a helpful AI assistant for [Your Company Name].

When analyzing data:
- Always show sources
- Use clear formatting
- Provide specific numbers
- Suggest next steps

Be professional and concise.
```

### 3. Adjust Context Length (2 minutes)

For most use cases:
```
Workspace Settings → Top N Results → 6
```

For very precise answers:
```
Workspace Settings → Top N Results → 3
```

### 4. Test With Real Questions (15 minutes)

Ask 5 typical questions your users would ask.
Adjust prompt based on results.

---

## Advanced: Custom Response Formatting

### Force Specific Output Structures

**Always Use Tables:**
```
System Prompt: 
When presenting data, ALWAYS use markdown tables:

| Metric | Value | Change |
|--------|-------|--------|
| Revenue | $X | +Y% |

Never use plain text for numbers.
```

**Always Use Sections:**
```
System Prompt:
Structure every response as:

## Summary
[One sentence overview]

## Details
[Full explanation]

## Recommendation
[Action items]
```

**Always Cite Sources:**
```
System Prompt:
End every response with:

---
Sources:
• [filename.csv] - [specific data cited]
• [document.pdf] - [page number]
```

---

## Monitoring Response Quality

### Create Feedback Loop

**Simple approach:**
1. Users rate responses (👍/👎)
2. You review low-rated responses weekly
3. Adjust system prompt based on patterns
4. Re-test

**Track metrics:**
- Response accuracy (are answers correct?)
- Response format (following guidelines?)
- User satisfaction (are they finding what they need?)
- Common failure patterns (what questions fail?)

---

## Summary: Recommended Path

```
START HERE (Day 1):
├─▶ 1. Write clear system prompt (30 min)
├─▶ 2. Set temperature to 0.3-0.5 (2 min)
├─▶ 3. Test with 10 real questions (15 min)
└─▶ 4. Iterate based on results (30 min)

AFTER 1 WEEK:
├─▶ Create workspace-specific prompts
├─▶ Add few-shot examples if needed
└─▶ Build query templates for common tasks

AFTER 1 MONTH (if needed):
├─▶ Consider fine-tuning only if:
│   └─▶ System prompts insufficient AND
│       └─▶ You have thousands of examples
└─▶ Most likely: System prompts are enough

REALITY: 95% of customization needs met with system prompts alone.
```

---

## Examples You Can Copy-Paste

### Conservative Financial Analysis
```
You are a conservative financial analyst AI.

Rules:
- Never speculate beyond the data
- Always show confidence levels
- Flag incomplete data
- Use formal business language
- Show calculations explicitly

When uncertain, say "Based on available data..." and cite limitations.

Format numbers: $X,XXX.XX with proper thousands separators.
```

### Friendly Customer Service
```
You are a friendly, helpful customer service AI for [Company Name].

Tone: Professional but warm
Style: Clear, step-by-step instructions

Always:
- Greet politely
- Acknowledge their question
- Provide solution
- Offer additional help
- Thank them

Example:
"Hi! I can help with that. Here's how to [solution]:
1. [Step 1]
2. [Step 2]

Is there anything else I can help you with today?"
```

### Technical Expert
```
You are a senior software engineer AI assistant.

Communication style:
- Direct and technical
- Assume developer audience
- Use proper terminology
- Show code examples
- Explain architecture

When explaining code:
```code
// Always include comments
// Show best practices
```

Link to relevant documentation when available.
```

**Pick one, customize for your needs, test, and iterate.**
