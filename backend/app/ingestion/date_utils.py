
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dateutil import parser as date_parser
from dateutil.parser import ParserError

logger = logging.getLogger(__name__)

# Only map unambiguous timezone abbreviations globally.
TZINFOS = {
    "UTC": timezone.utc,
    "GMT": timezone.utc,
    "Z": timezone.utc,
}

# Configure only when a publisher's timezone is known.
# Keys should match the publisher/feed identifier used by your pipeline.
FEED_TIMEZONES = {
    # "publisher_india": "Asia/Kolkata",
    # "publisher_uk": "Europe/London",
    # "publisher_japan": "Asia/Tokyo",
}


def parse_date_to_utc(
    date_str: Optional[str],
    feed_id: Optional[str] = None,
):
    """
    Parse a publication date and convert it to UTC.

    Returns:
        (utc_iso_string, epoch_timestamp)

    Returns (None, None) if the date is missing, invalid,
    or timezone information cannot be determined safely.
    """

    if not date_str or not str(date_str).strip():
        return None, None

    raw_date = str(date_str).strip()

    try:
        dt = date_parser.parse(
            raw_date,
            tzinfos=TZINFOS,
        )

        # Handle dates without timezone information.
        if dt.tzinfo is None:
            timezone_name = FEED_TIMEZONES.get(feed_id)

            if not timezone_name:
                logger.warning(
                    "Timezone missing for publication date. "
                    "Feed: %s | Date: %s",
                    feed_id,
                    raw_date,
                )
                return None, None

            try:
                source_timezone = ZoneInfo(timezone_name)
            except ZoneInfoNotFoundError:
                logger.error(
                    "Invalid timezone configuration: %s",
                    timezone_name,
                )
                return None, None

            dt = dt.replace(tzinfo=source_timezone)

        # Normalize to UTC.
        utc_dt = dt.astimezone(timezone.utc)

        epoch_timestamp = utc_dt.timestamp()

        if not math.isfinite(epoch_timestamp):
            return None, None

        return utc_dt.isoformat(), epoch_timestamp

    except (
        ParserError,
        ValueError,
        TypeError,
        OverflowError,
    ) as exc:
        logger.warning(
            "Could not parse publication date: %s | Error: %s",
            raw_date,
            exc,
        )
        return None, None


def get_cutoff_timestamp(retention_days: int = 30) -> float:
    """
    Return the UTC epoch timestamp for the retention cutoff.
    """

    if retention_days < 0:
        raise ValueError("retention_days cannot be negative")

    cutoff_date = (
        datetime.now(timezone.utc)
        - timedelta(days=retention_days)
    )

    return cutoff_date.timestamp()


def is_within_retention_window(
    epoch_ts: Optional[float],
    retention_days: int = 30,
) -> bool:
    """
    Check whether an article falls within the retention window.
    """

    if epoch_ts is None:
        return False

    if isinstance(epoch_ts, bool):
        return False

    try:
        timestamp = float(epoch_ts)
    except (TypeError, ValueError):
        return False

    if not math.isfinite(timestamp) or timestamp <= 0:
        return False

    cutoff_timestamp = get_cutoff_timestamp(retention_days)

    return timestamp >= cutoff_timestamp
