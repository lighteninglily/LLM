"""
SQL Agent - Uses local LLM to generate SQL queries from natural language
Enhanced with Semantic Layer for improved query accuracy.
"""

import json
import logging
import os
import re
from typing import Dict, Any, Optional, List
import httpx

from .database import get_schema_info, execute_safe_query, get_distinct_values

# Semantic layer path
SEMANTIC_LAYER_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "semantic_layer.json")
_semantic_layer_cache: dict = None

logger = logging.getLogger(__name__)

# vLLM endpoint
VLLM_ENDPOINT = "http://localhost:8000/v1/chat/completions"
MODEL_NAME = "Qwen/Qwen2.5-14B-Instruct-AWQ"

# Machine name aliases - map common shorthand to full database names
MACHINE_ALIASES = {
    "mmw": "CLIFFORD_MMW",
    "clifford mmw": "CLIFFORD_MMW",
    "clifford_mmw": "CLIFFORD_MMW",
    "mwpa": "CLIFFORD_MWPA",
    "clifford mwpa": "CLIFFORD_MWPA",
    "clw12": "CLIFFORD_CLW12",
    "clw12-2": "CLIFFORD_CLW12_2",
    "clw 12": "CLIFFORD_CLW12",
    "galv 1": "GALV_LINE_1",
    "galv 2": "GALV_LINE_2",
    "galv 3": "GALV_LINE_3",
    "galv line 1": "GALV_LINE_1",
    "galv line 2": "GALV_LINE_2",
    "galv line 3": "GALV_LINE_3",
    "drawing 1": "DRAWING_GZ1",
    "drawing 2": "DRAWING_GZ2",
    "drawing 3": "DRAWING_GZ3",
    "gz1": "DRAWING_GZ1",
    "gz2": "DRAWING_GZ2",
    "gz3": "DRAWING_GZ3",
    "schlatter": "SCHLATTER_PG28",
    "pg28": "SCHLATTER_PG28",
    "pg12": "SCHLATTER_PG12",
    "roll form": "ROLL_FORM",
    "rollform": "ROLL_FORM",
    "mesh trim": "MESH_TRIM",
    "flok": "FLOK_WELD",
    "anneal": "ANNLD_WIRE",
    "annealed": "ANNLD_WIRE",
    "ausro": "AUSRO",
}


def load_semantic_layer() -> Optional[dict]:
    """Load semantic layer from file if available."""
    global _semantic_layer_cache
    
    if _semantic_layer_cache is not None:
        return _semantic_layer_cache
    
    if os.path.exists(SEMANTIC_LAYER_PATH):
        try:
            with open(SEMANTIC_LAYER_PATH, 'r') as f:
                _semantic_layer_cache = json.load(f)
                logger.info("Loaded semantic layer from file")
                return _semantic_layer_cache
        except Exception as e:
            logger.warning(f"Failed to load semantic layer: {e}")
    
    return None


def get_aliases_from_semantic_layer() -> Dict[str, str]:
    """Extract aliases from semantic layer glossary."""
    layer = load_semantic_layer()
    if not layer:
        return {}
    
    aliases = {}
    # Add glossary terms as aliases
    for term, definition in layer.get("glossary", {}).items():
        aliases[term.lower()] = definition
    
    # Add column aliases from tables
    for table_name, table in layer.get("tables", {}).items():
        for col_name, col in table.get("columns", {}).items():
            for alias, value in col.get("aliases", {}).items():
                aliases[alias.lower()] = value
    
    return aliases


def normalize_question(question: str) -> str:
    """Replace machine aliases with full database names in the question."""
    normalized = question
    question_lower = question.lower()
    
    # Skip normalization if question already contains a proper machine name (UPPERCASE_WITH_UNDERSCORES)
    if re.search(r'[A-Z]+_[A-Z0-9]+', question):
        return question
    
    # Combine static aliases with semantic layer aliases
    all_aliases = {**MACHINE_ALIASES}
    semantic_aliases = get_aliases_from_semantic_layer()
    all_aliases.update(semantic_aliases)
    
    # Sort aliases by length (longest first) to avoid partial replacements
    sorted_aliases = sorted(all_aliases.items(), key=lambda x: len(x[0]), reverse=True)
    
    for alias, full_name in sorted_aliases:
        # Use word boundary matching to avoid partial replacements
        pattern = re.compile(r'\b' + re.escape(alias) + r'\b', re.IGNORECASE)
        if pattern.search(normalized):
            normalized = pattern.sub(full_name, normalized)
    
    return normalized


def get_schema_context_from_semantic_layer() -> Optional[str]:
    """Build schema context from semantic layer if available."""
    layer = load_semantic_layer()
    if not layer or not layer.get("tables"):
        return None
    
    lines = [f"ASW STEEL & WIRE DATABASE - SEMANTIC LAYER ENHANCED"]
    lines.append("")
    lines.append("=== TABLES ===")
    lines.append("")
    
    for i, (table_name, table) in enumerate(layer.get("tables", {}).items(), 1):
        desc = table.get("description", "")
        row_count = table.get("row_count", 0)
        time_col = table.get("time_column", "")
        
        lines.append(f"{i}. {table_name.upper()} ({row_count:,} rows) - {desc}")
        
        # Columns with types
        cols = []
        for col_name, col in table.get("columns", {}).items():
            cols.append(col_name)
        lines.append(f"   Columns: {', '.join(cols)}")
        
        # Time column warning
        if time_col:
            lines.append(f"   Date column: {time_col}")
        elif table_name.lower() == "inventory":
            lines.append(f"   NOTE: No date column - current snapshot only!")
        
        # Sample values for key columns
        for col_name, col in list(table.get("columns", {}).items())[:3]:
            samples = col.get("sample_values", [])
            if samples and col_name not in ["id", "created_at", "source_file"]:
                lines.append(f"   {col_name} samples: {', '.join(str(s)[:30] for s in samples[:5])}")
        
        # Query examples
        examples = table.get("query_examples", [])
        if examples:
            lines.append(f"   Example: {examples[0].get('sql', '')[:80]}")
        
        lines.append("")
    
    # Relationships
    rels = layer.get("relationships", [])
    if rels:
        lines.append("=== RELATIONSHIPS ===")
        for rel in rels[:5]:
            lines.append(f"   {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}")
        lines.append("")
    
    # Skip glossary in context - can confuse the LLM
    # Glossary is used for alias resolution in normalize_question() instead
    
    lines.append("=== RULES ===")
    lines.append("- KEEP QUERIES SIMPLE - query ONE table at a time, NO JOINS unless explicitly asked")
    lines.append("- Dates: 'YYYY-MM-DD' format, use BETWEEN for ranges")
    lines.append("- Machine names: UPPERCASE_WITH_UNDERSCORES")
    lines.append("- Always add LIMIT 50 unless counting/summing")
    lines.append("- PARTIAL MATCHING: Use LIKE with wildcards for text searches")
    lines.append("")
    lines.append("=== COMMON QUERY PATTERNS ===")
    lines.append("-- Top customers by sales:")
    lines.append("SELECT customer_name, SUM(sales_amount) as total FROM sales GROUP BY customer_name ORDER BY total DESC LIMIT 10")
    lines.append("-- Production by machine:")
    lines.append("SELECT machine, SUM(quantity) as total FROM production GROUP BY machine ORDER BY total DESC")
    lines.append("-- Current inventory:")
    lines.append("SELECT warehouse, part_description, quantity_available FROM inventory WHERE quantity_available > 0 LIMIT 50")
    
    return "\n".join(lines)


def get_schema_context() -> str:
    """Build comprehensive schema context for the LLM.
    Uses semantic layer if available, falls back to manual schema.
    """
    # Temporarily use manual schema - semantic layer context needs tuning for local LLM
    # TODO: Re-enable semantic layer after improving context format for Qwen model
    logger.info("Using manual schema context")
    schema = get_schema_info()
    
    # Get sample distinct values for key columns
    try:
        machines = get_distinct_values("production", "machine", 15)
        products = get_distinct_values("production", "product", 10)
        customers = get_distinct_values("sales", "customer_name", 10)
        warehouses = get_distinct_values("inventory", "warehouse", 10)
    except:
        machines, products, customers, warehouses = [], [], [], []
    
    context = f"""ASW STEEL & WIRE DATABASE - 33,872 RECORDS

=== TABLES ===

1. PRODUCTION (5,576 rows) - Daily manufacturing output
   Columns: date, machine, product, product_code, order_number, quantity, quantity_day, quantity_achieved, kg_per_sheet, sheets_per_hour, planned_total, actual_total
   Key machines: {', '.join(machines[:8]) if machines else 'CLIFFORD_MMW, CLIFFORD_MWPA, GALV_LINE_1, GALV_LINE_2, DRAWING_GZ1, SCHLATTER_PG28'}

2. SALES (24,908 rows) - Customer sales transactions
   Columns: date, customer_name, customer_group, product_number, product_desc, sales_qty, sales_kg, sales_amount, invoice, salesperson, market_type, state, country
   Sample customers: {', '.join(str(c)[:25] for c in customers[:4]) if customers else 'Various'}

3. INVENTORY (2,246 rows) - Current stock levels
   Columns: warehouse, warehouse_desc, warehouse_name, product_group, part_code, part_description, quantity, quantity_available, quantity_reserved, uom
   Use for: stock on hand, inventory by warehouse, available quantities
   NOTE: Use warehouse column for warehouse codes (M1, M2, etc.) e.g., WHERE warehouse = 'M1'

4. OPEN_ORDERS (246 rows) - Outstanding CUSTOMER orders
   Columns: order_date, due_date, order_number, customer, customer_group, product, product_desc, ordered_qty, outstanding_qty, ordered_amount, warehouse
   Use for: customer orders, due dates, what customers have ordered

5. PURCHASE_ORDERS (896 rows) - Supplier/vendor orders (NOT customer orders)
   Columns: order_date, required_date, po_number, vendor, part_code, part_desc, order_qty, outstanding_qty, warehouse
   Use for: supplier POs, vendor orders, incoming materials
   NOTE: Do NOT join with open_orders - these are separate systems

=== SIMPLE QUERY EXAMPLES ===

-- Production by machine in November 2025:
SELECT machine, SUM(quantity) as total FROM production WHERE date BETWEEN '2025-11-01' AND '2025-11-30' GROUP BY machine ORDER BY total DESC

-- Top 10 customers by sales:
SELECT customer_name, SUM(sales_amount) as total FROM sales GROUP BY customer_name ORDER BY total DESC LIMIT 10

-- Top selling products (use product_desc NOT product):
SELECT product_desc, SUM(sales_amount) as total_sales, SUM(sales_qty) as total_qty FROM sales GROUP BY product_desc ORDER BY total_sales DESC LIMIT 10

-- Inventory by warehouse (use warehouse column for M1, M2, etc.):
SELECT warehouse, part_description, quantity_available FROM inventory WHERE warehouse = 'M1' LIMIT 50

-- Open orders (use due_date column):
SELECT customer, product_desc, due_date, outstanding_qty FROM open_orders ORDER BY due_date LIMIT 50

-- Purchase orders / parts waiting to receive (use required_date NOT due_date):
SELECT vendor, part_desc, outstanding_qty, required_date FROM purchase_orders WHERE outstanding_qty > 0 ORDER BY required_date LIMIT 50

=== RULES ===
- KEEP QUERIES SIMPLE - no subqueries or complex joins
- Dates: 'YYYY-MM-DD' format, use BETWEEN for ranges
- Machine names: UPPERCASE_WITH_UNDERSCORES
- Always add LIMIT unless counting/summing
- PARTIAL MATCHING: For product codes, part codes, or text searches, ALWAYS use LIKE with wildcards:
  * part_code LIKE '%4524%' (finds any code containing 4524)
  * product LIKE '%IMG%' (finds products with IMG anywhere)
  * customer_name LIKE '%STEEL%' (partial customer name match)
"""
    # Add uploaded tables if any
    try:
        from api.upload import get_uploaded_tables_schema
        uploaded_schema = get_uploaded_tables_schema()
        if uploaded_schema:
            context += uploaded_schema
    except ImportError:
        pass
    
    return context


def post_process_sql(sql: str, question: str) -> str:
    """Remove unwanted WHERE clauses that the LLM adds incorrectly."""
    question_lower = question.lower()
    
    # Keywords that indicate user wants a filter
    filter_keywords = [
        'nsw', 'qld', 'vic', 'queensland', 'new south wales', 'victoria',
        'western australia', 'tasmania', 'in australia', 'perth',
        'brisbane', 'adelaide', 'sydney', 'melbourne', 'usa', 'america',
        'south australia', 'kentucky', 'pennsylvania', 'ohio', 'georgia'
    ]
    
    # "breakdown by state" or "by state" means GROUP BY state, not filter by specific state
    is_groupby_state = 'by state' in question_lower or 'breakdown' in question_lower
    
    # Check if user actually asked for a state/location filter (specific state name)
    user_wants_filter = any(kw in question_lower for kw in filter_keywords) and not is_groupby_state
    
    if not user_wants_filter:
        # Remove state-related WHERE clauses that LLM added incorrectly
        import re
        # Patterns to match various state/country filters
        patterns = [
            # Remove AND state = 'xxx' or AND country = 'xxx'
            r"\s+AND\s+state\s*=\s*'[^']*'",
            r"\s+AND\s+state\s+LIKE\s+'[^']*'",
            r"\s+AND\s+country\s*=\s*'[^']*'",
            r"\s+AND\s+country\s+LIKE\s+'[^']*'",
            r"\s+AND\s+customer_name\s*=\s*'[^']*'",
            r"\s+AND\s+customer_name\s+LIKE\s+'[^']*'",
            r"\s+AND\s+product_desc\s*=\s*'[^']*'",
            r"\s+AND\s+product_desc\s+LIKE\s+'[^']*'",
            # Remove WHERE state = 'xxx' (when it's the only condition)
            r"\s+WHERE\s+state\s*=\s*'[^']*'",
            r"\s+WHERE\s+state\s+LIKE\s+'[^']*'",
            r"\s+WHERE\s+country\s*=\s*'[^']*'",
            r"\s+WHERE\s+country\s+LIKE\s+'[^']*'",
        ]
        
        original_sql = sql
        for pattern in patterns:
            sql = re.sub(pattern, '', sql, flags=re.IGNORECASE)
        
        if sql != original_sql:
            logger.info(f"Post-processed SQL: removed unwanted WHERE clause")
    
    return sql


def build_sql_prompt(question: str) -> str:
    """Build the prompt for SQL generation."""
    schema_context = get_schema_context()
    
    prompt = f"""{schema_context}

=== USER QUESTION ===
{question}

=== GENERATE SQL ===
Write ONE SQLite query. Output ONLY SQL, nothing else.

FORBIDDEN:
- NO WHERE clause unless user mentions a filter
- NO JOIN
- NO subqueries

SQL:"""
    return prompt


async def generate_sql(question: str) -> Dict[str, Any]:
    """Use LLM to generate SQL from natural language question."""
    # Normalize question to replace aliases with full machine names
    normalized_question = normalize_question(question)
    logger.info(f"Normalized question: {normalized_question}")
    
    prompt = build_sql_prompt(normalized_question)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                VLLM_ENDPOINT,
                json={
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": "You are a SQL expert. Generate only valid SQLite queries. No explanations."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500,
                }
            )
            response.raise_for_status()
            result = response.json()
            
            sql = result["choices"][0]["message"]["content"].strip()
            
            # Clean up the SQL
            sql = sql.replace("```sql", "").replace("```", "").strip()
            
            # Remove any leading/trailing quotes
            if sql.startswith('"') and sql.endswith('"'):
                sql = sql[1:-1]
            if sql.startswith("'") and sql.endswith("'"):
                sql = sql[1:-1]
            
            # Post-process: remove unwanted WHERE clauses if user didn't ask for filters
            sql = post_process_sql(sql, question)
            
            return {"sql": sql, "error": None}
            
    except Exception as e:
        logger.error(f"LLM SQL generation failed: {e}")
        return {"sql": None, "error": str(e)}


async def query_with_sql(question: str) -> Dict[str, Any]:
    """Generate SQL and execute query."""
    # Generate SQL
    sql_result = await generate_sql(question)
    
    if sql_result["error"]:
        return {
            "success": False,
            "error": sql_result["error"],
            "sql": None,
            "results": [],
            "answer": None
        }
    
    sql = sql_result["sql"]
    
    # Check if response doesn't look like SQL
    if not sql.upper().strip().startswith("SELECT"):
        return {
            "success": False,
            "error": "invalid_sql_generated",
            "sql": sql,
            "results": [],
            "answer": None,
            "use_rag": True
        }
    
    # Execute the query
    query_result = execute_safe_query(sql)
    
    if query_result["error"]:
        return {
            "success": False,
            "error": query_result["error"],
            "sql": sql,
            "results": [],
            "answer": None
        }
    
    return {
        "success": True,
        "error": None,
        "sql": sql,
        "results": query_result["results"],
        "row_count": query_result["row_count"],
        "answer": None  # Will be formatted by response generator
    }


async def format_sql_response(question: str, sql_result: Dict[str, Any]) -> str:
    """Use LLM to format SQL results into natural language."""
    if not sql_result["success"] or not sql_result["results"]:
        return None
    
    # Limit results for context
    results = sql_result["results"][:50]
    row_count = sql_result["row_count"]
    
    # Detect result type for better formatting guidance
    num_cols = len(results[0]) if results else 0
    has_amount = any('amount' in k.lower() or 'total' in k.lower() or 'price' in k.lower() for k in (results[0].keys() if results else []))
    has_qty = any('qty' in k.lower() or 'quantity' in k.lower() or 'count' in k.lower() for k in (results[0].keys() if results else []))
    
    results_str = json.dumps(results, indent=2, default=str)
    
    # Build format hint based on data type
    if row_count == 1 and num_cols <= 2:
        format_hint = "SINGLE VALUE - State the answer directly in one sentence."
    elif row_count <= 10 and num_cols >= 2:
        format_hint = "TABLE FORMAT - Use markdown table with | and ---"
    elif row_count > 10:
        format_hint = "SUMMARY TABLE - Show top 10 in markdown table, mention total count"
    else:
        format_hint = "LIST FORMAT - Use bullet points"
    
    prompt = f"""Format these SQL results as a clean markdown table.

QUESTION: {question}
ROWS: {row_count}

DATA:
{results_str}

FORMAT: {format_hint}

STRICT FORMATTING RULES:
1. TABLE STRUCTURE (REQUIRED):
   | Column Name | Column Name |
   |-------------|-------------|
   | value       | value       |

2. COLUMN HEADERS:
   - Replace underscores with spaces
   - Use Title Case (e.g., "sales_amount" → "Sales Amount")
   - Keep headers SHORT (max 20 chars)

3. NUMBER FORMATTING:
   - Money/amounts/totals/prices: $1,234,567.89
   - Quantities/counts: 1,234,567
   - Percentages: 45.2%
   - Decimals: max 2 places

4. ALIGNMENT (in your output):
   - Right-align all numbers
   - Left-align text

5. OUTPUT RULES:
   - Start DIRECTLY with the table (no intro text)
   - If showing subset, add: "*Showing X of Y results*" at end
   - NO explanations before or after unless specifically asked
   - NO "Here are the results" or similar phrases

EXAMPLE OUTPUT:
| Customer | Sales Amount | Quantity |
|----------|-------------:|---------:|
| ACME Corp | $125,432.50 | 2,340 |
| Beta Inc | $98,210.00 | 1,890 |

Output:"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                VLLM_ENDPOINT,
                json={
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": "You are a data formatting assistant. Output clean, well-formatted markdown. For tables, ALWAYS use | column | separators and |---| header dividers. Format numbers with commas and currency with $."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1500,
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Failed to format response: {e}")
        # Fallback: generate basic table
        return generate_fallback_table(results, row_count)


def generate_fallback_table(results: List[Dict], row_count: int) -> str:
    """Generate a well-formatted markdown table as fallback."""
    if not results:
        return "No results found."
    
    # Get headers
    headers = list(results[0].keys())
    
    # Detect column types for alignment
    col_types = {}
    for h in headers:
        sample = results[0].get(h, "")
        is_numeric = isinstance(sample, (int, float))
        is_money = is_numeric and any(kw in h.lower() for kw in ['amount', 'total', 'price', 'cost', 'revenue', 'sales'])
        is_qty = is_numeric and any(kw in h.lower() for kw in ['qty', 'quantity', 'count', 'units', 'outstanding'])
        col_types[h] = {'numeric': is_numeric, 'money': is_money, 'qty': is_qty}
    
    # Build table
    lines = []
    
    # Format header names
    formatted_headers = []
    for h in headers:
        name = h.replace("_", " ").title()
        if len(name) > 25:
            name = name[:22] + "..."
        formatted_headers.append(name)
    
    # Header row
    header_row = "| " + " | ".join(formatted_headers) + " |"
    lines.append(header_row)
    
    # Separator with alignment hints
    sep_parts = []
    for h in headers:
        if col_types[h]['numeric']:
            sep_parts.append("---:")  # Right-align numbers
        else:
            sep_parts.append("---")   # Left-align text
    sep_row = "|" + "|".join(sep_parts) + "|"
    lines.append(sep_row)
    
    # Data rows (limit to 20)
    for row in results[:20]:
        values = []
        for h in headers:
            v = row.get(h, "")
            if v is None:
                values.append("-")
            elif col_types[h]['money']:
                values.append(f"${float(v):,.2f}")
            elif col_types[h]['qty']:
                if isinstance(v, float) and v == int(v):
                    values.append(f"{int(v):,}")
                elif isinstance(v, float):
                    values.append(f"{v:,.1f}")
                else:
                    values.append(f"{int(v):,}")
            elif isinstance(v, float):
                values.append(f"{v:,.2f}")
            elif isinstance(v, int):
                values.append(f"{v:,}")
            else:
                text = str(v)
                if len(text) > 40:
                    text = text[:37] + "..."
                values.append(text)
        lines.append("| " + " | ".join(values) + " |")
    
    # Add total row for numeric columns if applicable
    if row_count <= 20 and len(results) > 1:
        has_summable = any(col_types[h]['money'] or col_types[h]['qty'] for h in headers)
        if has_summable:
            total_values = []
            for h in headers:
                if col_types[h]['money']:
                    total = sum(float(r.get(h, 0) or 0) for r in results)
                    total_values.append(f"**${total:,.2f}**")
                elif col_types[h]['qty']:
                    total = sum(float(r.get(h, 0) or 0) for r in results)
                    total_values.append(f"**{total:,.0f}**")
                elif headers.index(h) == 0:
                    total_values.append("**Total**")
                else:
                    total_values.append("")
            lines.append("| " + " | ".join(total_values) + " |")
    
    if row_count > 20:
        lines.append(f"\n*Showing 20 of {row_count:,} total results*")
    
    return "\n".join(lines)


def classify_query(question: str) -> str:
    """Quick classification of query type without LLM call."""
    question_lower = question.lower()
    
    # SQL indicators (data queries) - weighted by specificity
    sql_keywords = [
        # High confidence SQL terms
        'how many', 'how much', 'total', 'count', 'sum', 'average', 'avg',
        'list all', 'show all', 'show me', 'give me',
        # Data-specific terms
        'produced', 'production', 'sold', 'sales', 'selling', 'revenue',
        'quantity', 'qty', 'amount', 'volume', 'units',
        # Time-based queries
        'between', 'during', 'in november', 'in december', 'last month', 'this month', 'last year',
        # Ranking queries
        'top', 'highest', 'lowest', 'most', 'least', 'best', 'worst', 'biggest', 'smallest',
        # Entity queries
        'orders', 'inventory', 'stock', 'customers', 'customer', 'products', 'product',
        'machines', 'machine', 'warehouse', 'vendor', 'supplier',
        # Comparison queries
        'compare', 'vs', 'versus', 'difference', 'by month', 'by customer', 'by machine',
        'grouped by', 'group by', 'per', 'breakdown'
    ]
    
    # RAG indicators (knowledge/policy queries)
    rag_keywords = [
        'policy', 'procedure', 'process', 'guideline', 'rule', 'regulation',
        'how do i', 'how does the', 'explain', 'describe', 'tell me about',
        'what is the policy', 'what is the procedure', 'what are the rules',
        'help me understand', 'meaning', 'definition', 'purpose', 'reason',
        'why do we', 'why does', 'handbook', 'manual', 'documentation',
        'sick leave', 'annual leave', 'vacation', 'holiday', 'benefits',
        'disciplinary', 'whistleblower', 'hr', 'human resources', 'employee'
    ]
    
    # Check for explicit RAG patterns first (policy questions)
    rag_patterns = [
        'what is the policy', 'what is the procedure', 'explain the',
        'tell me about the policy', 'sick leave', 'annual leave',
        'disciplinary', 'whistleblower', 'handbook'
    ]
    for pattern in rag_patterns:
        if pattern in question_lower:
            return "rag"
    
    # Check for explicit SQL patterns (data questions)
    sql_patterns = [
        'top selling', 'best selling', 'most sold', 'highest sales',
        'top customers', 'top products', 'top machines',
        'how many', 'how much', 'total sales', 'total production',
        'in stock', 'inventory level', 'what did we produce', 'what did we sell',
        'parts are we waiting', 'waiting to receive', 'purchase orders', 'open pos',
        'high sales', 'low inventory', 'outstanding', 'vendors', 'suppliers',
        'uploaded', 'upload', 'my file', 'the file', 'i just uploaded', 'csv', 'excel',
        'spreadsheet', 'imported', 'my data', 'the data i'
    ]
    for pattern in sql_patterns:
        if pattern in question_lower:
            return "sql"
    
    # Score-based classification
    sql_score = sum(1 for kw in sql_keywords if kw in question_lower)
    rag_score = sum(1 for kw in rag_keywords if kw in question_lower)
    
    # Bonus for "what are the" + data term (likely SQL)
    if 'what are the' in question_lower or 'what is the' in question_lower:
        data_terms = ['product', 'customer', 'order', 'sale', 'machine', 'inventory']
        if any(term in question_lower for term in data_terms):
            sql_score += 2
    
    if sql_score > rag_score:
        return "sql"
    elif rag_score > sql_score:
        return "rag"
    else:
        # Default to SQL for ambiguous queries
        return "sql"
