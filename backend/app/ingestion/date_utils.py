"""
Date parsing and 30-day retention window validation.
Ensures missing or invalid publication dates are NOT treated as current news.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from dateutil import parser as date_parser


def parse_date_to_utc(date_str: Optional[str]) -> tuple[Optional[str], Optional[float]]:
    """
    Parses RSS pubDate string into ISO 8601 string and epoch timestamp (UTC).
    Returns (None, None) if date_str is missing, empty, or unparseable.
    
    CRITICAL: Never automatically fall back to current UTC time, so that
    missing or invalid dates cannot bypass the 30-day retention filter.
    """
    if not date_str or not str(date_str).strip():
        return None, None

    try:
        dt = date_parser.parse(str(date_str))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat(), dt.timestamp()
    except Exception:
        return None, None


def get_cutoff_timestamp(retention_days: int = 30) -> float:
    """Returns the UTC epoch timestamp cutoff for the retention window."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    return cutoff_date.timestamp()


def is_within_retention_window(epoch_ts: Optional[float], retention_days: int = 30) -> bool:
    """
    Checks whether an epoch timestamp is within the retention period.
    Returns False if epoch_ts is None or invalid.
    """
    if epoch_ts is None or epoch_ts <= 0:
        return False
    return epoch_ts >= get_cutoff_timestamp(retention_days)
