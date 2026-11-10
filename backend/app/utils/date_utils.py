import time
from datetime import datetime, timezone, timedelta
from typing import Optional
from dateutil import parser as date_parser

def parse_date_to_utc(date_str: Optional[str] = None) -> datetime:
    """
    Parses arbitrary date strings from RSS feeds into a timezone-aware UTC datetime.
    Falls back to current UTC time if date_str is empty or unparseable.
    """
    if not date_str:
        return datetime.now(timezone.utc)

    try:
        dt = date_parser.parse(date_str)
        if dt.tzinfo is None:
            # Assume UTC if no timezone is provided
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)

def datetime_to_epoch(dt: datetime) -> float:
    """Converts a UTC datetime object to epoch timestamp (seconds)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()

def get_cutoff_timestamp(retention_days: int = 30) -> float:
    """
    Returns the UTC epoch timestamp for retention cutoff.
    Any article with published_timestamp < cutoff_timestamp is expired.
    """
    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=retention_days)
    return cutoff_dt.timestamp()

def is_within_retention_window(dt: datetime, retention_days: int = 30) -> bool:
    """Checks whether an article's publication date is within the retention window."""
    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=retention_days)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= cutoff_dt

def format_iso_utc(dt: datetime) -> str:
    """Formats datetime as ISO 8601 string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

