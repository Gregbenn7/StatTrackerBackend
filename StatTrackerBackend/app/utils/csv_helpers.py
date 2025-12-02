"""CSV parsing and normalization utilities."""


def normalize_column_name(col: str) -> str:
    """
    Normalize column names to lowercase and stripped.
    
    Args:
        col: Column name to normalize
        
    Returns:
        Normalized column name
    """
    if col is None:
        return ""
    return str(col).strip().lower()


def parse_decimal(value) -> float | None:
    """
    Helper to convert things like '.333' or '1.250' into float or None.
    Handles NaN / missing gracefully.
    
    Args:
        value: Value to parse
        
    Returns:
        Float value or None if invalid/missing
    """
    if value is None:
        return None
    try:
        s = str(value).strip()
        if s == "" or s.lower() == "nan":
            return None
        # HitTrax sometimes uses '.333' style strings; float() handles that.
        return float(s)
    except Exception:
        return None

