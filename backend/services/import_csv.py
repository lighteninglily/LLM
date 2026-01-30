"""
Import CSV files into SQLite database
"""

import pandas as pd
from pathlib import Path
import sqlite3
import logging
from datetime import datetime
import re

from .database import get_connection, init_database, DB_PATH

logger = logging.getLogger(__name__)

# Base directory for CSV files
CSV_BASE = Path(__file__).parent.parent.parent


def normalize_machine_name(filename: str) -> str:
    """Extract and normalize machine name from filename."""
    # Pattern: "Daily Production Report v1.xlsm_Machine Name.csv"
    match = re.search(r'xlsm_(.+)\.csv$', filename)
    if match:
        name = match.group(1)
        # Normalize to uppercase with underscores
        return name.upper().replace(' ', '_').replace('-', '_')
    return filename


def parse_date(date_val) -> str:
    """Parse various date formats to ISO format."""
    if pd.isna(date_val):
        return None
    
    if isinstance(date_val, datetime):
        return date_val.strftime('%Y-%m-%d')
    
    date_str = str(date_val).strip()
    
    # Try various formats
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y/%m/%d',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.split()[0], fmt.split()[0]).strftime('%Y-%m-%d')
        except:
            continue
    
    return date_str[:10] if len(date_str) >= 10 else None


def import_production_csv(csv_path: Path, conn: sqlite3.Connection):
    """Import a daily production report CSV."""
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as e:
        logger.error(f"Failed to read {csv_path}: {e}")
        return 0
    
    machine = normalize_machine_name(csv_path.name)
    source_file = csv_path.name
    
    # Map column names (handle variations)
    col_map = {
        'date': ['date', 'Date', 'DATE'],
        'product': ['dmw_product', 'product', 'Product', 'PRODUCT'],
        'product_code': ['ross_code', 'product_code', 'Part Code', 'part_code'],
        'order_number': ['ross_order', 'order', 'Order', 'order_number'],
        'quantity': ['qty', 'quantity', 'Qty', 'QTY'],
        'quantity_day': ['qty_day', 'Qty Day'],
        'quantity_achieved': ['achieved', 'Achieved'],
        'kg_per_sheet': ['kg_sht', 'kg_pce', 'kg_per_sheet'],
        'sheets_per_hour': ['sheets_per_hour', 'pcs_hr'],
        'planned_total': ['planned_totals', 'plan_totals_kg'],
        'actual_total': ['act_totals', 'act_totals_kg'],
    }
    
    def get_col(df, names):
        for name in names:
            if name in df.columns:
                return df[name]
        return None
    
    records = []
    for _, row in df.iterrows():
        date_val = None
        for col in col_map['date']:
            if col in df.columns:
                date_val = parse_date(row.get(col))
                break
        
        if not date_val:
            continue
        
        record = {
            'date': date_val,
            'machine': machine,
            'product': None,
            'product_code': None,
            'order_number': None,
            'quantity': None,
            'quantity_day': None,
            'quantity_achieved': None,
            'kg_per_sheet': None,
            'sheets_per_hour': None,
            'planned_total': None,
            'actual_total': None,
            'source_file': source_file,
        }
        
        for field, cols in col_map.items():
            if field == 'date':
                continue
            for col in cols:
                if col in df.columns and pd.notna(row.get(col)):
                    record[field] = row.get(col)
                    break
        
        records.append(record)
    
    if records:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO production (date, machine, product, product_code, order_number,
                quantity, quantity_day, quantity_achieved, kg_per_sheet, sheets_per_hour,
                planned_total, actual_total, source_file)
            VALUES (:date, :machine, :product, :product_code, :order_number,
                :quantity, :quantity_day, :quantity_achieved, :kg_per_sheet, :sheets_per_hour,
                :planned_total, :actual_total, :source_file)
        """, records)
        conn.commit()
    
    return len(records)


def import_sales_csv(csv_path: Path, conn: sqlite3.Connection):
    """Import sales data CSV."""
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as e:
        logger.error(f"Failed to read {csv_path}: {e}")
        return 0
    
    source_file = csv_path.name
    records = []
    
    for _, row in df.iterrows():
        date_val = parse_date(row.get('Trans Date'))
        if not date_val:
            continue
        
        record = {
            'date': date_val,
            'customer_name': row.get('Customer Name'),
            'customer_group': row.get('Customer Group'),
            'product_number': row.get('Product Number'),
            'product_desc': row.get('Product Desc'),
            'sales_qty': row.get('Sales Qty'),
            'sales_kg': row.get('Sales Kg'),
            'sales_amount': row.get('Product Sales'),
            'invoice': row.get('Invoice'),
            'salesperson': row.get('Salesperson'),
            'market_type': row.get('Market Type'),
            'state': row.get('State/Province'),
            'country': row.get('Country'),
            'source_file': source_file,
        }
        records.append(record)
    
    if records:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO sales (date, customer_name, customer_group, product_number, product_desc,
                sales_qty, sales_kg, sales_amount, invoice, salesperson, market_type, state, country, source_file)
            VALUES (:date, :customer_name, :customer_group, :product_number, :product_desc,
                :sales_qty, :sales_kg, :sales_amount, :invoice, :salesperson, :market_type, :state, :country, :source_file)
        """, records)
        conn.commit()
    
    return len(records)


def import_inventory_csv(csv_path: Path, conn: sqlite3.Connection):
    """Import inventory CSV."""
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as e:
        logger.error(f"Failed to read {csv_path}: {e}")
        return 0
    
    source_file = csv_path.name
    records = []
    
    for _, row in df.iterrows():
        record = {
            'warehouse': row.get('Warehouse'),
            'warehouse_desc': row.get('Warehouse Desc'),
            'product_group': row.get('Product Group Desc'),
            'part_code': row.get('Part Code'),
            'part_description': row.get('Part Description'),
            'quantity': row.get('IC Quantity'),
            'quantity_available': row.get('IC Qty Available'),
            'quantity_reserved': row.get('IC Qty Reserved'),
            'uom': row.get('UOM'),
            'source_file': source_file,
        }
        records.append(record)
    
    if records:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO inventory (warehouse, warehouse_desc, product_group, part_code, part_description,
                quantity, quantity_available, quantity_reserved, uom, source_file)
            VALUES (:warehouse, :warehouse_desc, :product_group, :part_code, :part_description,
                :quantity, :quantity_available, :quantity_reserved, :uom, :source_file)
        """, records)
        conn.commit()
    
    return len(records)


def import_open_orders_csv(csv_path: Path, conn: sqlite3.Connection):
    """Import open sales orders CSV."""
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as e:
        logger.error(f"Failed to read {csv_path}: {e}")
        return 0
    
    source_file = csv_path.name
    records = []
    
    for _, row in df.iterrows():
        order_date = parse_date(row.get('Order Date'))
        due_date = parse_date(row.get('Due Date'))
        
        record = {
            'order_date': order_date,
            'due_date': due_date,
            'order_number': row.get('Order Number'),
            'customer': row.get('Customer'),
            'customer_group': row.get('Customer Group'),
            'product': row.get('Product'),
            'product_desc': row.get('Description'),
            'ordered_qty': row.get('Ordered Qty'),
            'outstanding_qty': row.get('Outstanding Qty'),
            'ordered_amount': row.get('Ordered $AUD'),
            'warehouse': row.get('Warehouse'),
            'source_file': source_file,
        }
        records.append(record)
    
    if records:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO open_orders (order_date, due_date, order_number, customer, customer_group,
                product, product_desc, ordered_qty, outstanding_qty, ordered_amount, warehouse, source_file)
            VALUES (:order_date, :due_date, :order_number, :customer, :customer_group,
                :product, :product_desc, :ordered_qty, :outstanding_qty, :ordered_amount, :warehouse, :source_file)
        """, records)
        conn.commit()
    
    return len(records)


def import_purchase_orders_csv(csv_path: Path, conn: sqlite3.Connection):
    """Import purchase orders CSV."""
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as e:
        logger.error(f"Failed to read {csv_path}: {e}")
        return 0
    
    source_file = csv_path.name
    records = []
    
    for _, row in df.iterrows():
        order_date = parse_date(row.get('Order Date'))
        required_date = parse_date(row.get('Required Date'))
        
        record = {
            'order_date': order_date,
            'required_date': required_date,
            'po_number': row.get('PO #'),
            'vendor': row.get('Vendor'),
            'part_code': row.get('Part Code'),
            'part_desc': row.get('Part Desc'),
            'order_qty': row.get('Order Qty'),
            'outstanding_qty': row.get('Outstanding Qty'),
            'warehouse': row.get('WH'),
            'source_file': source_file,
        }
        records.append(record)
    
    if records:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO purchase_orders (order_date, required_date, po_number, vendor, part_code,
                part_desc, order_qty, outstanding_qty, warehouse, source_file)
            VALUES (:order_date, :required_date, :po_number, :vendor, :part_code,
                :part_desc, :order_qty, :outstanding_qty, :warehouse, :source_file)
        """, records)
        conn.commit()
    
    return len(records)


def import_all_csvs(csv_dirs: list = None):
    """Import all CSVs from specified directories."""
    if csv_dirs is None:
        csv_dirs = [
            CSV_BASE / "v2_batch1",
            CSV_BASE / "v2_batch2",
            CSV_BASE / "v2_batch3",
        ]
    
    # Initialize database
    init_database()
    conn = get_connection()
    
    # Clear existing data
    cursor = conn.cursor()
    for table in ['production', 'sales', 'inventory', 'open_orders', 'purchase_orders']:
        cursor.execute(f"DELETE FROM {table}")
    conn.commit()
    
    stats = {
        'production': 0,
        'sales': 0,
        'inventory': 0,
        'open_orders': 0,
        'purchase_orders': 0,
    }
    
    for csv_dir in csv_dirs:
        if not csv_dir.exists():
            logger.warning(f"Directory not found: {csv_dir}")
            continue
        
        for csv_file in csv_dir.glob("*.csv"):
            filename = csv_file.name.lower()
            
            # Route to appropriate importer based on filename
            if 'daily production' in filename or 'production sheet' in filename:
                count = import_production_csv(csv_file, conn)
                stats['production'] += count
                logger.info(f"Imported {count} production records from {csv_file.name}")
            
            elif 'sales' in filename and 'credit' in filename:
                count = import_sales_csv(csv_file, conn)
                stats['sales'] += count
                logger.info(f"Imported {count} sales records from {csv_file.name}")
            
            elif 'inventory' in filename:
                count = import_inventory_csv(csv_file, conn)
                stats['inventory'] += count
                logger.info(f"Imported {count} inventory records from {csv_file.name}")
            
            elif 'open sales orders' in filename:
                count = import_open_orders_csv(csv_file, conn)
                stats['open_orders'] += count
                logger.info(f"Imported {count} open orders from {csv_file.name}")
            
            elif 'open po' in filename:
                count = import_purchase_orders_csv(csv_file, conn)
                stats['purchase_orders'] += count
                logger.info(f"Imported {count} purchase orders from {csv_file.name}")
    
    conn.close()
    
    print("\n=== Import Summary ===")
    for table, count in stats.items():
        print(f"  {table}: {count} records")
    print(f"\nDatabase: {DB_PATH}")
    
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import_all_csvs()
