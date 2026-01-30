"""
Data Enhancer - Cleans and enhances database for better LLM querying
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "production.db")

# Warehouse code to full name mapping
WAREHOUSE_NAMES = {
    "M1": "ASW Perth",
    "M2": "ASW Brisbane", 
    "M3": "ASW Adelaide",
    "M4": "Wynyard Contracting Services",
    "M5": "CSPD Paddington Gold",
    "M6": "MJB Industries",
    "M7": "Cornwall Coal Blackwood Collie",
    "MM": "ASW Direct Ship Malaysia",
    "MT": "ASW Goods in Transit Overseas"
}

# Machine code to friendly name
MACHINE_NAMES = {
    "ANNLD_WIRE": "Annealed Wire Line",
    "AUSRO": "Australian Roll Former",
    "CLIFFORD_CLW12": "Clifford CLW12 Wire Drawer",
    "CLIFFORD_CLW12_2": "Clifford CLW12 Wire Drawer #2",
    "CLIFFORD_MMW": "Clifford Multi-Wire Machine",
    "CLIFFORD_MWPA": "Clifford MWPA Line",
    "DRAWING_GZ1": "Wire Drawing GZ Line 1",
    "DRAWING_GZ2": "Wire Drawing GZ Line 2",
    "DRAWING_GZ3": "Wire Drawing GZ Line 3",
    "FLOK_WELD": "Flok Welder",
    "GALV_LINE_1": "Galvanizing Line 1",
    "GALV_LINE_2": "Galvanizing Line 2",
    "GALV_LINE_3": "Galvanizing Line 3",
    "MESH_TRIM": "Mesh Trimmer",
    "ROLL_FORM": "Roll Former"
}


def trim_all_text_columns(conn):
    """Trim whitespace from all text columns in all tables"""
    cur = conn.cursor()
    
    # Get all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
    tables = [r[0] for r in cur.fetchall()]
    
    total_updated = 0
    for table in tables:
        # Get text columns
        cur.execute(f"PRAGMA table_info({table})")
        text_cols = [c[1] for c in cur.fetchall() if c[2].upper() in ('TEXT', 'VARCHAR', '')]
        
        for col in text_cols:
            # Trim whitespace
            cur.execute(f"UPDATE {table} SET {col} = TRIM({col}) WHERE {col} != TRIM({col})")
            updated = cur.rowcount
            if updated > 0:
                print(f"  Trimmed {updated} values in {table}.{col}")
                total_updated += updated
    
    conn.commit()
    return total_updated


def add_friendly_columns(conn):
    """Add friendly name columns for coded values"""
    cur = conn.cursor()
    
    # Add warehouse_name column to inventory if not exists
    try:
        cur.execute("ALTER TABLE inventory ADD COLUMN warehouse_name TEXT")
        print("  Added inventory.warehouse_name column")
    except:
        pass  # Column already exists
    
    # Populate warehouse names
    for code, name in WAREHOUSE_NAMES.items():
        cur.execute("UPDATE inventory SET warehouse_name = ? WHERE warehouse = ?", (name, code))
    print(f"  Updated {len(WAREHOUSE_NAMES)} warehouse names")
    
    # Add machine_name column to production if not exists
    try:
        cur.execute("ALTER TABLE production ADD COLUMN machine_name TEXT")
        print("  Added production.machine_name column")
    except:
        pass  # Column already exists
    
    # Populate machine names
    for code, name in MACHINE_NAMES.items():
        cur.execute("UPDATE production SET machine_name = ? WHERE machine = ?", (name, code))
    print(f"  Updated {len(MACHINE_NAMES)} machine names")
    
    conn.commit()


def enhance_database():
    """Run all enhancements"""
    print(f"Enhancing database: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    
    print("\nStep 1: Trimming whitespace...")
    trimmed = trim_all_text_columns(conn)
    print(f"  Total trimmed: {trimmed}")
    
    print("\nStep 2: Adding friendly name columns...")
    add_friendly_columns(conn)
    
    print("\nStep 3: Verifying...")
    cur = conn.cursor()
    
    # Check inventory
    cur.execute("SELECT warehouse, warehouse_name FROM inventory LIMIT 3")
    print("  Inventory samples:")
    for r in cur.fetchall():
        print(f"    {r[0]} -> {r[1]}")
    
    # Check production
    cur.execute("SELECT machine, machine_name FROM production LIMIT 3")
    print("  Production samples:")
    for r in cur.fetchall():
        print(f"    {r[0]} -> {r[1]}")
    
    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    enhance_database()
