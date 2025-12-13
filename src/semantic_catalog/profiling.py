import re
from datetime import datetime

def infer_semantic_type(values):
    """
    Infers the semantic type of a list of values.
    Returns: 'boolean', 'numeric', 'date', 'code', 'text', or 'unknown'
    """
    clean_values = [v for v in values if v is not None]
    if not clean_values:
        return "empty"

    # Check for Boolean
    if all(str(v).lower() in ['true', 'false', '0', '1', 't', 'f', 'yes', 'no'] for v in clean_values):
        return "boolean"

    # Check for Numeric
    is_numeric = all(isinstance(v, (int, float)) or str(v).replace('.', '', 1).isdigit() for v in clean_values)
    if is_numeric:
        return "numeric"

    # Check for Date (Simple regex YYYY-MM-DD or MM/DD/YYYY)
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',
        r'\d{2}/\d{2}/\d{4}'
    ]
    is_date = all(any(re.match(pat, str(v)) for pat in date_patterns) for v in clean_values)
    if is_date:
        return "date"
        
    # Check for short codes (e.g., country codes)
    if all(len(str(v)) <= 5 and str(v).isupper() for v in clean_values):
        return "code"

    return "text"

def profile_column(data_sample):
    """
    Analyzes a sample of data from a column.
    """
    unique_values = set(data_sample)
    cardinality_raw = len(unique_values)
    
    # Infer cardinality label based on sample size (heuristic)
    # If sample is small (e.g. 5), cardinality might be misleading, but we do best effort.
    # Usually we profile with larger samples, but here we assume 'data_sample' is what we have.
    sample_size = len(data_sample)
    cardinality_label = "low"
    if sample_size > 0 and cardinality_raw / sample_size > 0.8:
        cardinality_label = "high"
        
    semantic_type = infer_semantic_type(data_sample)
    
    return {
        "inferred_type": semantic_type,
        "cardinality": cardinality_label,
        "sample_values": list(unique_values)[:5] # Keep a few for context
    }

