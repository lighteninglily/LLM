#!/usr/bin/env python3
"""
Entity Normalizer - Standardizes entity names for consistent KG extraction.
"""

import re
from typing import Dict, Optional

# Company name mappings (lowercase -> canonical)
COMPANY_MAPPINGS = {
    # SOUTH32 variants
    "south32": "SOUTH32",
    "south 32": "SOUTH32",
    "s32": "SOUTH32",
    "south32 limited": "SOUTH32",
    "south 32 limited": "SOUTH32",
    # BHP variants
    "bhp": "BHP",
    "bhp billiton": "BHP",
    "bhpb": "BHP",
    "bhp group": "BHP",
    # GLENCORE variants
    "glencore": "GLENCORE",
    "glencore coal": "GLENCORE",
    "glencore australia": "GLENCORE",
    # ANGLO variants
    "anglo american": "ANGLO AMERICAN",
    "anglo": "ANGLO AMERICAN",
    "anglo coal": "ANGLO AMERICAN",
    # Others
    "peabody": "PEABODY ENERGY",
    "peabody energy": "PEABODY ENERGY",
    "yancoal": "YANCOAL",
    "yancoal australia": "YANCOAL",
    "whitehaven": "WHITEHAVEN COAL",
    "whitehaven coal": "WHITEHAVEN COAL",
    "centennial": "CENTENNIAL COAL",
    "centennial coal": "CENTENNIAL COAL",
    "centennial myuna": "CENTENNIAL MYUNA",
    "centennial mandalong": "CENTENNIAL MANDALONG",
    "springvale": "SPRINGVALE COAL",
    "springvale coal": "SPRINGVALE COAL",
    "ashton": "ASHTON COAL",
    "ashton coal": "ASHTON COAL",
    "ashton coal operations": "ASHTON COAL",
    "fitzroy": "FITZROY RESOURCES",
    "fitzroy coal": "FITZROY RESOURCES",
    "jennmar": "JENNMAR",
    "jennmar australia": "JENNMAR",
    "asw": "ASW",
    "australian steel & wire": "ASW",
    "australian steel and wire": "ASW",
    # Additional mining companies
    "newcrest": "NEWCREST MINING",
    "newcrest mining": "NEWCREST MINING",
    "evolution": "EVOLUTION MINING",
    "evolution mining": "EVOLUTION MINING",
    "northern star": "NORTHERN STAR",
    "northern star resources": "NORTHERN STAR",
    "oz minerals": "OZ MINERALS",
    "ozminerals": "OZ MINERALS",
    "rio tinto": "RIO TINTO",
    "rio": "RIO TINTO",
    "fortescue": "FORTESCUE",
    "fmg": "FORTESCUE",
    "fortescue metals": "FORTESCUE",
}

# Mine site mappings
MINE_MAPPINGS = {
    "appin": "APPIN MINE, NSW",
    "appin mine": "APPIN MINE, NSW",
    "appin colliery": "APPIN MINE, NSW",
    "dendrobium": "DENDROBIUM MINE, NSW",
    "dendrobium mine": "DENDROBIUM MINE, NSW",
    "west cliff": "WEST CLIFF MINE, NSW",
    "westcliff": "WEST CLIFF MINE, NSW",
    "west cliff mine": "WEST CLIFF MINE, NSW",
    "bulli seam": "BULLI SEAM OPERATIONS, NSW",
    "bulli": "BULLI SEAM OPERATIONS, NSW",
    "metropolitan": "METROPOLITAN MINE, NSW",
    "metropolitan mine": "METROPOLITAN MINE, NSW",
    "tahmoor": "TAHMOOR MINE, NSW",
    "tahmoor mine": "TAHMOOR MINE, NSW",
    "springvale": "SPRINGVALE MINE, NSW",
    "springvale mine": "SPRINGVALE MINE, NSW",
    "mandalong": "MANDALONG MINE, NSW",
    "mandalong mine": "MANDALONG MINE, NSW",
    "myuna": "MYUNA MINE, NSW",
    "myuna mine": "MYUNA MINE, NSW",
    "narrabri": "NARRABRI MINE, NSW",
    "narrabri mine": "NARRABRI MINE, NSW",
    "maules creek": "MAULES CREEK MINE, NSW",
    "hunter valley": "HUNTER VALLEY OPERATIONS, NSW",
    "hvo": "HUNTER VALLEY OPERATIONS, NSW",
    "ravensworth": "RAVENSWORTH MINE, NSW",
    "mount thorley": "MT THORLEY MINE, NSW",
    "mt thorley": "MT THORLEY MINE, NSW",
    "warkworth": "WARKWORTH MINE, NSW",
    "bulga": "BULGA MINE, NSW",
    # QLD mines
    "moranbah": "MORANBAH MINE, QLD",
    "moranbah north": "MORANBAH NORTH MINE, QLD",
    "broadmeadow": "BROADMEADOW MINE, QLD",
    "goonyella": "GOONYELLA MINE, QLD",
    "peak downs": "PEAK DOWNS MINE, QLD",
    "saraji": "SARAJI MINE, QLD",
    "blackwater": "BLACKWATER MINE, QLD",
    "curragh": "CURRAGH MINE, QLD",
    "kestrel": "KESTREL MINE, QLD",
    "oaky creek": "OAKY CREEK MINE, QLD",
    "grasstree": "GRASSTREE MINE, QLD",
}

# Machine name mappings
MACHINE_MAPPINGS = {
    "schlatter pg12": "Schlatter PG12",
    "schlatter pg28": "Schlatter PG28",
    "pg12": "Schlatter PG12",
    "pg28": "Schlatter PG28",
    "roll form": "Roll Form Line",
    "rollform": "Roll Form Line",
    "mesh trim": "Mesh Trim Line",
    "meshtrim": "Mesh Trim Line",
    "drawing": "Drawing Line",
    "galv": "Galvanizing Line",
    "galvanizing": "Galvanizing Line",
    "galvanising": "Galvanizing Line",
    "clifford": "Clifford Machine",
    "annld": "Annealing Line",
    "annealing": "Annealing Line",
    "ausro": "Ausro Machine",
    "flok": "FLOK Machine",
}

# State abbreviations
STATE_MAPPINGS = {
    "nsw": "NSW",
    "new south wales": "NSW",
    "qld": "QLD",
    "queensland": "QLD",
    "vic": "VIC",
    "victoria": "VIC",
    "wa": "WA",
    "western australia": "WA",
    "sa": "SA",
    "south australia": "SA",
}


def normalize_company(name: str) -> str:
    """Normalize company name to canonical form."""
    if not name:
        return name
    lower = name.lower().strip()
    # Check direct mapping
    if lower in COMPANY_MAPPINGS:
        return COMPANY_MAPPINGS[lower]
    # Check partial matches
    for key, canonical in COMPANY_MAPPINGS.items():
        if key in lower:
            return canonical
    # Default: uppercase if looks like company name
    if len(name) <= 10 or name.isupper():
        return name.upper()
    return name


def normalize_mine(name: str) -> str:
    """Normalize mine site name."""
    if not name:
        return name
    lower = name.lower().strip()
    for key, canonical in MINE_MAPPINGS.items():
        if key in lower:
            return canonical
    # Add "Mine" suffix if not present
    if "mine" not in lower and "operations" not in lower:
        return f"{name.title()} Mine"
    return name.title()


def normalize_machine(name: str) -> str:
    """Normalize machine/equipment name."""
    if not name:
        return name
    lower = name.lower().strip()
    for key, canonical in MACHINE_MAPPINGS.items():
        if key in lower:
            return canonical
    return name.title()


def normalize_date(date_str: str) -> str:
    """Convert date to readable format."""
    if not date_str:
        return date_str
    
    # Common date patterns
    patterns = [
        (r"(\d{4})-(\d{2})-(\d{2})", "%Y-%m-%d"),
        (r"(\d{2})/(\d{2})/(\d{4})", "%d/%m/%Y"),
        (r"(\d{2})-(\d{2})-(\d{4})", "%d-%m-%Y"),
    ]
    
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    # Try YYYY-MM-DD
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(date_str))
    if match:
        year, month, day = match.groups()
        month_name = months[int(month) - 1]
        return f"{month_name} {int(day)}, {year}"
    
    # Try DD/MM/YYYY
    match = re.match(r"(\d{2})/(\d{2})/(\d{4})", str(date_str))
    if match:
        day, month, year = match.groups()
        month_name = months[int(month) - 1]
        return f"{month_name} {int(day)}, {year}"
    
    return date_str


def normalize_quantity(value, unit: str = "units") -> str:
    """Format quantity with commas and units."""
    try:
        num = float(value)
        if num == int(num):
            formatted = f"{int(num):,}"
        else:
            formatted = f"{num:,.2f}"
        return f"{formatted} {unit}"
    except (ValueError, TypeError):
        return str(value)


def normalize_record(record: Dict) -> Dict:
    """Normalize all entity fields in a record."""
    normalized = {}
    
    for key, value in record.items():
        if value is None or value == "":
            normalized[key] = value
            continue
            
        key_lower = key.lower()
        str_value = str(value).strip()
        
        # Detect and normalize based on field name
        if any(x in key_lower for x in ["customer", "company", "client", "buyer"]):
            normalized[key] = normalize_company(str_value)
        elif any(x in key_lower for x in ["mine", "site", "location", "destination"]):
            normalized[key] = normalize_mine(str_value)
        elif any(x in key_lower for x in ["machine", "equipment", "line"]):
            normalized[key] = normalize_machine(str_value)
        elif any(x in key_lower for x in ["date", "_dt", "timestamp"]):
            normalized[key] = normalize_date(str_value)
        elif any(x in key_lower for x in ["state", "region"]):
            lower_val = str_value.lower()
            normalized[key] = STATE_MAPPINGS.get(lower_val, str_value.upper())
        else:
            normalized[key] = value
    
    return normalized


def add_custom_mapping(category: str, key: str, canonical: str):
    """Add a custom mapping to the normalizer."""
    mappings = {
        "company": COMPANY_MAPPINGS,
        "mine": MINE_MAPPINGS,
        "machine": MACHINE_MAPPINGS,
        "state": STATE_MAPPINGS,
    }
    if category in mappings:
        mappings[category][key.lower()] = canonical


if __name__ == "__main__":
    # Test examples
    test_records = [
        {"customer": "south32", "mine": "appin", "date": "2025-01-15"},
        {"customer": "BHP Billiton", "machine": "pg12", "qty": 5000},
        {"company": "glencore", "site": "dendrobium", "state": "nsw"},
    ]
    
    for record in test_records:
        print(f"Original: {record}")
        print(f"Normalized: {normalize_record(record)}")
        print()
