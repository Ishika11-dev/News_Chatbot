"""
Date parsing and 30-day retention window validation.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from dateutil import parser as date_parser


def parse_date_to_utc(date_str: Optional[str]) -> tuple[str, float]:
    """
    Parses RSS pubDate string into ISO 8601 string and epoch timestamp (UTC).
    Falls back to current UTC time if date_str is missing or unparseable.
    """
    now_utc = datetime.now(timezone.utc)
    if not date_str:
        return now_utc.isoformat(), now_utc.timestamp()

    try:
        dt = date_parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat(), dt.timestamp()
    except Exception:
        return now_utc.isoformat(), now_utc.timestamp()


def get_cutoff_timestamp(retention_days: int = 30) -> float:
    """Returns the UTC epoch timestamp cutoff for the retention window."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    return cutoff_date.timestamp()


def is_within_retention_window(epoch_ts: float, retention_days: int = 30) -> bool:
    """Checks whether an epoch timestamp is within the retention period."""
    return epoch_ts >= get_cutoff_timestamp(retention_days)

