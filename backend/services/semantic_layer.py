"""
Semantic Layer Generator for Text-to-SQL
Based on M-Schema, Contextual-SQL, and industry best practices.

This module analyzes database schemas and data to generate rich semantic metadata
that dramatically improves LLM text-to-SQL accuracy.
"""

import sqlite3
import json
import os
import httpx
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import Counter
import re

# Local vLLM endpoint for Qwen
VLLM_ENDPOINT = "http://localhost:8000/v1/chat/completions"
MODEL_NAME = "Qwen/Qwen2.5-14B-Instruct-AWQ"


@dataclass
class ColumnProfile:
    """Profile of a single column"""
    name: str
    data_type: str
    description: str = ""
    sample_values: List[str] = None
    unique_count: int = 0
    null_count: int = 0
    total_count: int = 0
    null_rate: float = 0.0
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_ref: str = ""
    aliases: Dict[str, str] = None
    business_terms: List[str] = None
    
    def __post_init__(self):
        if self.sample_values is None:
            self.sample_values = []
        if self.aliases is None:
            self.aliases = {}
        if self.business_terms is None:
            self.business_terms = []


@dataclass
class TableProfile:
    """Profile of a single table"""
    name: str
    description: str = ""
    row_count: int = 0
    columns: Dict[str, ColumnProfile] = None
    business_terms: List[str] = None
    query_examples: List[Dict[str, str]] = None
    time_column: str = ""
    primary_key: str = ""
    
    def __post_init__(self):
        if self.columns is None:
            self.columns = {}
        if self.business_terms is None:
            self.business_terms = []
        if self.query_examples is None:
            self.query_examples = []


@dataclass
class Relationship:
    """Relationship between tables"""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: str = "many-to-one"
    confidence: float = 1.0


@dataclass 
class SemanticLayer:
    """Complete semantic layer for a database"""
    database_name: str
    tables: Dict[str, TableProfile] = None
    relationships: List[Relationship] = None
    glossary: Dict[str, str] = None
    generated_at: str = ""
    
    def __post_init__(self):
        if self.tables is None:
            self.tables = {}
        if self.relationships is None:
            self.relationships = []
        if self.glossary is None:
            self.glossary = {}


class DataProfiler:
    """Analyzes database schema and data to create profiles"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def get_tables(self) -> List[str]:
        """Get all table names"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """Get column information for a table"""
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "name": row[1],
                "type": row[2],
                "not_null": bool(row[3]),
                "default": row[4],
                "pk": bool(row[5])
            })
        return columns
    
    def get_row_count(self, table_name: str) -> int:
        """Get row count for a table"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    
    def get_sample_values(self, table_name: str, column_name: str, limit: int = 10) -> List[str]:
        """Get sample distinct values for a column"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"""
                SELECT DISTINCT "{column_name}" 
                FROM {table_name} 
                WHERE "{column_name}" IS NOT NULL 
                LIMIT {limit}
            """)
            values = [str(row[0]).strip() if row[0] else "" for row in cursor.fetchall()]
            return [v for v in values if v][:limit]
        except Exception as e:
            print(f"Error getting samples for {table_name}.{column_name}: {e}")
            return []
    
    def get_column_stats(self, table_name: str, column_name: str) -> Dict:
        """Get statistics for a column"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT "{column_name}") as unique_count,
                    SUM(CASE WHEN "{column_name}" IS NULL THEN 1 ELSE 0 END) as null_count
                FROM {table_name}
            """)
            row = cursor.fetchone()
            return {
                "total": row[0],
                "unique_count": row[1],
                "null_count": row[2]
            }
        except Exception as e:
            print(f"Error getting stats for {table_name}.{column_name}: {e}")
            return {"total": 0, "unique_count": 0, "null_count": 0}
    
    def profile_column(self, table_name: str, col_info: Dict) -> ColumnProfile:
        """Create a full profile for a column"""
        stats = self.get_column_stats(table_name, col_info["name"])
        samples = self.get_sample_values(table_name, col_info["name"])
        
        null_rate = stats["null_count"] / stats["total"] if stats["total"] > 0 else 0
        
        return ColumnProfile(
            name=col_info["name"],
            data_type=col_info["type"],
            sample_values=samples,
            unique_count=stats["unique_count"],
            null_count=stats["null_count"],
            total_count=stats["total"],
            null_rate=round(null_rate, 4),
            is_primary_key=col_info["pk"]
        )
    
    def profile_table(self, table_name: str) -> TableProfile:
        """Create a full profile for a table"""
        columns_info = self.get_table_info(table_name)
        row_count = self.get_row_count(table_name)
        
        columns = {}
        primary_key = ""
        time_column = ""
        
        for col_info in columns_info:
            col_profile = self.profile_column(table_name, col_info)
            columns[col_info["name"]] = col_profile
            
            if col_info["pk"]:
                primary_key = col_info["name"]
            
            # Detect time columns
            if col_info["name"].lower() in ["date", "datetime", "timestamp", "created_at", "order_date", "due_date"]:
                if not time_column:
                    time_column = col_info["name"]
        
        return TableProfile(
            name=table_name,
            row_count=row_count,
            columns=columns,
            primary_key=primary_key,
            time_column=time_column
        )
    
    def profile_database(self) -> Dict[str, TableProfile]:
        """Profile all tables in the database"""
        tables = {}
        for table_name in self.get_tables():
            print(f"  Profiling table: {table_name}")
            tables[table_name] = self.profile_table(table_name)
        return tables
    
    def close(self):
        self.conn.close()


class RelationshipDetector:
    """Detects relationships between tables"""
    
    def __init__(self, tables: Dict[str, TableProfile]):
        self.tables = tables
    
    def detect_by_naming(self) -> List[Relationship]:
        """Detect relationships by column naming conventions"""
        relationships = []
        
        # Common FK patterns: table_id, table_code, table_name
        for table_name, table_profile in self.tables.items():
            for col_name, col_profile in table_profile.columns.items():
                col_lower = col_name.lower()
                
                # Check for _id, _code patterns
                for suffix in ["_id", "_code", "_number"]:
                    if col_lower.endswith(suffix):
                        potential_table = col_lower.replace(suffix, "")
                        # Check if matches another table
                        for other_table in self.tables.keys():
                            if other_table.lower() == potential_table or \
                               other_table.lower().startswith(potential_table):
                                # Found potential relationship
                                relationships.append(Relationship(
                                    from_table=table_name,
                                    from_column=col_name,
                                    to_table=other_table,
                                    to_column=self._find_matching_column(other_table, col_name),
                                    confidence=0.7
                                ))
        
        return relationships
    
    def detect_by_value_overlap(self) -> List[Relationship]:
        """Detect relationships by comparing sample values"""
        relationships = []
        
        # Compare sample values between columns
        for t1_name, t1_profile in self.tables.items():
            for c1_name, c1_profile in t1_profile.columns.items():
                if not c1_profile.sample_values:
                    continue
                    
                c1_values = set(c1_profile.sample_values)
                
                for t2_name, t2_profile in self.tables.items():
                    if t1_name == t2_name:
                        continue
                        
                    for c2_name, c2_profile in t2_profile.columns.items():
                        if not c2_profile.sample_values:
                            continue
                        
                        c2_values = set(c2_profile.sample_values)
                        
                        # Check overlap
                        overlap = c1_values & c2_values
                        if len(overlap) >= 3:  # At least 3 common values
                            overlap_ratio = len(overlap) / min(len(c1_values), len(c2_values))
                            if overlap_ratio >= 0.5:
                                relationships.append(Relationship(
                                    from_table=t1_name,
                                    from_column=c1_name,
                                    to_table=t2_name,
                                    to_column=c2_name,
                                    confidence=round(overlap_ratio, 2)
                                ))
        
        return relationships
    
    def _find_matching_column(self, table_name: str, source_col: str) -> str:
        """Find the most likely matching column in target table"""
        table = self.tables.get(table_name)
        if not table:
            return ""
        
        # Try exact match first
        if source_col in table.columns:
            return source_col
        
        # Try common patterns
        source_lower = source_col.lower()
        for col_name in table.columns.keys():
            col_lower = col_name.lower()
            if col_lower == source_lower:
                return col_name
            if "code" in source_lower and "code" in col_lower:
                return col_name
            if "id" in source_lower and "id" in col_lower:
                return col_name
        
        # Return primary key if available
        if table.primary_key:
            return table.primary_key
            
        return ""
    
    def detect_all(self) -> List[Relationship]:
        """Detect all relationships"""
        all_rels = []
        all_rels.extend(self.detect_by_naming())
        all_rels.extend(self.detect_by_value_overlap())
        
        # Deduplicate
        seen = set()
        unique_rels = []
        for rel in all_rels:
            key = (rel.from_table, rel.from_column, rel.to_table, rel.to_column)
            if key not in seen:
                seen.add(key)
                unique_rels.append(rel)
        
        return unique_rels


class SemanticEnricher:
    """Uses local Qwen LLM via vLLM to enrich semantic metadata"""
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.client = httpx.Client(timeout=60.0)
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """Call local Qwen LLM via vLLM endpoint"""
        try:
            response = self.client.post(
                VLLM_ENDPOINT,
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"LLM call failed: {e}")
            return None
    
    def enrich_table(self, table: TableProfile) -> TableProfile:
        """Enrich a table with LLM-generated metadata"""
        if not self.use_llm:
            return self._enrich_table_heuristic(table)
        
        # Build context for LLM
        columns_info = []
        for col_name, col in table.columns.items():
            samples = col.sample_values[:5] if col.sample_values else []
            columns_info.append(f"- {col_name} ({col.data_type}): samples={samples}")
        
        prompt = f"""Analyze this database table and provide semantic metadata.

Table: {table.name}
Row count: {table.row_count}
Columns:
{chr(10).join(columns_info)}

Output JSON only, no explanation:
{{"table_description": "brief description", "business_terms": ["term1", "term2"], "columns": {{"column_name": {{"description": "what it is", "business_terms": ["term"]}}}}}}"""

        result_text = self._call_llm(prompt)
        if not result_text:
            return self._enrich_table_heuristic(table)
        
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            
            # Apply enrichments
            table.description = result.get("table_description", "")
            table.business_terms = result.get("business_terms", [])
            
            for col_name, col_meta in result.get("columns", {}).items():
                if col_name in table.columns:
                    table.columns[col_name].description = col_meta.get("description", "")
                    table.columns[col_name].business_terms = col_meta.get("business_terms", [])
                    table.columns[col_name].aliases = col_meta.get("aliases", {})
            
            return table
            
        except Exception as e:
            print(f"JSON parse failed for {table.name}: {e}")
            return self._enrich_table_heuristic(table)
    
    def _enrich_table_heuristic(self, table: TableProfile) -> TableProfile:
        """Fallback heuristic enrichment without LLM"""
        name_lower = table.name.lower()
        
        # Table descriptions based on common names
        descriptions = {
            "production": "Daily manufacturing output records by machine and product",
            "sales": "Customer sales transactions with amounts and quantities",
            "inventory": "Current stock levels by warehouse and product (snapshot, no dates)",
            "open_orders": "Outstanding customer orders awaiting fulfillment",
            "purchase_orders": "Supplier purchase orders for incoming materials",
            "customers": "Customer master data",
            "products": "Product catalog",
        }
        
        table.description = descriptions.get(name_lower, f"Data table: {table.name}")
        
        # Generate business terms from table name
        terms = name_lower.replace("_", " ").split()
        table.business_terms = terms
        
        # Column descriptions based on common patterns
        for col_name, col in table.columns.items():
            col_lower = col_name.lower()
            
            if "date" in col_lower:
                col.description = "Date field"
                col.business_terms = ["date", "time", "when"]
            elif "amount" in col_lower or "price" in col_lower:
                col.description = "Monetary amount"
                col.business_terms = ["money", "cost", "value", "dollars"]
            elif "qty" in col_lower or "quantity" in col_lower:
                col.description = "Quantity/count"
                col.business_terms = ["count", "number", "how many"]
            elif "name" in col_lower:
                col.description = "Name identifier"
            elif "code" in col_lower or "id" in col_lower:
                col.description = "Unique identifier code"
            elif "desc" in col_lower:
                col.description = "Description text"
        
        return table
    
    def generate_glossary(self, tables: Dict[str, TableProfile]) -> Dict[str, str]:
        """Generate a business glossary from all tables"""
        glossary = {}
        
        # Common manufacturing/business abbreviations
        known_terms = {
            "MMW": "Clifford MMW Wire Machine",
            "MWPA": "Clifford MWPA Wire Machine", 
            "GZ": "Drawing Machine (Galvanizing Zone)",
            "GALV": "Galvanizing Line",
            "QTY": "Quantity",
            "PO": "Purchase Order",
            "SO": "Sales Order",
            "WH": "Warehouse",
            "INV": "Inventory",
            "PROD": "Production",
            "NSW": "New South Wales",
            "QLD": "Queensland",
            "VIC": "Victoria",
            "WA": "Western Australia",
            "SA": "South Australia",
        }
        glossary.update(known_terms)
        
        # Extract aliases from columns
        for table in tables.values():
            for col in table.columns.values():
                glossary.update(col.aliases)
        
        return glossary
    
    def generate_query_examples(self, table: TableProfile) -> List[Dict[str, str]]:
        """Generate example queries for a table"""
        examples = []
        name = table.name
        
        # Find key columns
        date_col = table.time_column
        numeric_cols = [c for c, p in table.columns.items() 
                       if p.data_type in ("REAL", "INTEGER", "NUMERIC") 
                       and "id" not in c.lower()]
        text_cols = [c for c, p in table.columns.items() 
                    if p.data_type == "TEXT" and p.unique_count > 1 and p.unique_count < 100]
        
        # Basic count
        examples.append({
            "question": f"How many records in {name}?",
            "sql": f"SELECT COUNT(*) FROM {name}"
        })
        
        # Group by text column
        if text_cols:
            col = text_cols[0]
            examples.append({
                "question": f"Count by {col}",
                "sql": f"SELECT {col}, COUNT(*) as count FROM {name} GROUP BY {col} ORDER BY count DESC LIMIT 10"
            })
        
        # Sum numeric column
        if numeric_cols:
            col = numeric_cols[0]
            examples.append({
                "question": f"Total {col}",
                "sql": f"SELECT SUM({col}) as total FROM {name}"
            })
            
            # Group by + sum
            if text_cols:
                examples.append({
                    "question": f"Top {text_cols[0]} by {col}",
                    "sql": f"SELECT {text_cols[0]}, SUM({col}) as total FROM {name} GROUP BY {text_cols[0]} ORDER BY total DESC LIMIT 10"
                })
        
        # Date filter
        if date_col:
            examples.append({
                "question": f"{name} in November 2025",
                "sql": f"SELECT * FROM {name} WHERE {date_col} BETWEEN '2025-11-01' AND '2025-11-30' LIMIT 50"
            })
        
        return examples


class SemanticLayerGenerator:
    """Main class to generate complete semantic layer"""
    
    def __init__(self, db_path: str, use_llm: bool = True):
        self.db_path = db_path
        self.profiler = DataProfiler(db_path)
        self.enricher = SemanticEnricher(use_llm=use_llm)
        self.use_llm = use_llm
        
    def generate(self, use_llm: bool = None) -> SemanticLayer:
        """Generate complete semantic layer"""
        from datetime import datetime
        
        # Use instance setting if not overridden
        if use_llm is None:
            use_llm = self.use_llm
        
        print("Step 1: Profiling database...")
        tables = self.profiler.profile_database()
        
        print("Step 2: Detecting relationships...")
        detector = RelationshipDetector(tables)
        relationships = detector.detect_all()
        
        print("Step 3: Enriching with semantic metadata...")
        for table_name, table_profile in tables.items():
            print(f"  Enriching: {table_name}")
            if use_llm:
                tables[table_name] = self.enricher.enrich_table(table_profile)
            else:
                tables[table_name] = self.enricher._enrich_table_heuristic(table_profile)
            
            # Generate query examples
            tables[table_name].query_examples = self.enricher.generate_query_examples(table_profile)
        
        print("Step 4: Building glossary...")
        glossary = self.enricher.generate_glossary(tables)
        
        print("Step 5: Assembling semantic layer...")
        layer = SemanticLayer(
            database_name=os.path.basename(self.db_path),
            tables=tables,
            relationships=relationships,
            glossary=glossary,
            generated_at=datetime.now().isoformat()
        )
        
        self.profiler.close()
        print("Done!")
        
        return layer
    
    def to_json(self, layer: SemanticLayer) -> str:
        """Convert semantic layer to JSON"""
        def serialize(obj):
            if hasattr(obj, '__dict__'):
                return {k: serialize(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize(i) for i in obj]
            else:
                return obj
        
        return json.dumps(serialize(layer), indent=2)
    
    def save(self, layer: SemanticLayer, output_path: str):
        """Save semantic layer to file"""
        with open(output_path, 'w') as f:
            f.write(self.to_json(layer))
        print(f"Saved to: {output_path}")
    
    @staticmethod
    def load(path: str) -> dict:
        """Load semantic layer from file"""
        with open(path, 'r') as f:
            return json.load(f)


def generate_mschema_format(layer: SemanticLayer) -> str:
    """Generate M-Schema format string for LLM prompts"""
    lines = [f"Database: {layer.database_name}"]
    lines.append("")
    
    for table_name, table in layer.tables.items():
        lines.append(f"Table: {table_name}, {table.description}")
        lines.append(f"  Row count: {table.row_count}")
        if table.time_column:
            lines.append(f"  Time column: {table.time_column}")
        lines.append("  Columns:")
        
        for col_name, col in table.columns.items():
            pk_marker = " [PK]" if col.is_primary_key else ""
            samples = ", ".join(col.sample_values[:5]) if col.sample_values else "N/A"
            lines.append(f"    - {col_name} ({col.data_type}){pk_marker}: {col.description}")
            lines.append(f"      Samples: {samples}")
            if col.aliases:
                aliases_str = ", ".join(f"{k}→{v}" for k, v in col.aliases.items())
                lines.append(f"      Aliases: {aliases_str}")
        
        if table.query_examples:
            lines.append("  Example queries:")
            for ex in table.query_examples[:3]:
                lines.append(f"    Q: {ex['question']}")
                lines.append(f"    SQL: {ex['sql']}")
        
        lines.append("")
    
    if layer.relationships:
        lines.append("Relationships:")
        for rel in layer.relationships:
            lines.append(f"  {rel.from_table}.{rel.from_column} → {rel.to_table}.{rel.to_column}")
        lines.append("")
    
    if layer.glossary:
        lines.append("Glossary:")
        for term, definition in list(layer.glossary.items())[:20]:
            lines.append(f"  {term}: {definition}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Test the generator
    db_path = "../data/production.db"
    generator = SemanticLayerGenerator(db_path)
    layer = generator.generate(use_llm=False)
    generator.save(layer, "../data/semantic_layer.json")
    print("\n" + "="*60)
    print("M-Schema Format:")
    print("="*60)
    print(generate_mschema_format(layer))
