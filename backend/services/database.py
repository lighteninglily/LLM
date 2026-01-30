"""
SQLite Database for Production Data
Hybrid SQL + RAG system - SQL for structured queries, RAG for context
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "data" / "production.db"


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory for dict-like access."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Production records table (daily production reports)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS production (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            machine TEXT,
            product TEXT,
            product_code TEXT,
            order_number TEXT,
            quantity REAL,
            quantity_day REAL,
            quantity_achieved REAL,
            kg_per_sheet REAL,
            sheets_per_hour REAL,
            planned_total REAL,
            actual_total REAL,
            source_file TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Sales records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            customer_name TEXT,
            customer_group TEXT,
            product_number TEXT,
            product_desc TEXT,
            sales_qty REAL,
            sales_kg REAL,
            sales_amount REAL,
            invoice TEXT,
            salesperson TEXT,
            market_type TEXT,
            state TEXT,
            country TEXT,
            source_file TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Inventory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse TEXT,
            warehouse_desc TEXT,
            product_group TEXT,
            part_code TEXT,
            part_description TEXT,
            quantity REAL,
            quantity_available REAL,
            quantity_reserved REAL,
            uom TEXT,
            source_file TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Open orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS open_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_date DATE,
            due_date DATE,
            order_number TEXT,
            customer TEXT,
            customer_group TEXT,
            product TEXT,
            product_desc TEXT,
            ordered_qty REAL,
            outstanding_qty REAL,
            ordered_amount REAL,
            warehouse TEXT,
            source_file TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Purchase orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_date DATE,
            required_date DATE,
            po_number TEXT,
            vendor TEXT,
            part_code TEXT,
            part_desc TEXT,
            order_qty REAL,
            outstanding_qty REAL,
            warehouse TEXT,
            source_file TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for fast queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_date ON production(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_machine ON production(machine)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_product ON production(product)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_part ON inventory(part_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_date ON open_orders(order_date)")
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


def execute_query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a SQL query and return results as list of dicts."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"SQL Error: {e}\nQuery: {sql}")
        raise
    finally:
        conn.close()


def execute_safe_query(sql: str) -> Dict[str, Any]:
    """Execute a read-only query with safety checks."""
    # Basic SQL injection prevention
    sql_lower = sql.lower().strip()
    
    # Only allow SELECT queries
    if not sql_lower.startswith("select"):
        return {"error": "Only SELECT queries are allowed", "results": []}
    
    # Block dangerous keywords
    dangerous = ["drop", "delete", "update", "insert", "alter", "create", "truncate", ";--"]
    for keyword in dangerous:
        if keyword in sql_lower:
            return {"error": f"Query contains forbidden keyword: {keyword}", "results": []}
    
    try:
        results = execute_query(sql)
        return {"results": results, "row_count": len(results), "error": None}
    except Exception as e:
        return {"error": str(e), "results": []}


def get_schema_info() -> str:
    """Get database schema information for LLM context."""
    conn = get_connection()
    cursor = conn.cursor()
    
    schema_info = []
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        col_info = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
        schema_info.append(f"- {table} ({count} rows): {col_info}")
    
    conn.close()
    return "\n".join(schema_info)


def get_sample_data(table: str, limit: int = 3) -> List[Dict]:
    """Get sample data from a table."""
    return execute_query(f"SELECT * FROM {table} LIMIT ?", (limit,))


def get_distinct_values(table: str, column: str, limit: int = 20) -> List[str]:
    """Get distinct values for a column."""
    results = execute_query(
        f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL LIMIT ?",
        (limit,)
    )
    return [r[column] for r in results]


if __name__ == "__main__":
    init_database()
    print(f"Database created at {DB_PATH}")
    print("\nSchema:")
    print(get_schema_info())
