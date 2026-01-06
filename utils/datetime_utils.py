from datetime import datetime, timezone
from typing import Optional


def make_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert naive datetime to timezone-aware (UTC).
    If already aware, return as is.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Naive datetime, assume UTC
        return dt. replace(tzinfo=timezone.utc)
    return dt


def make_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert timezone-aware datetime to naive (UTC).
    If already naive, return as is.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # Aware datetime, convert to UTC and remove tzinfo
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def now_utc() -> datetime:
    """Get current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)


def calculate_duration(start: datetime, end:  datetime) -> int:
    """
    Calculate duration in seconds between two datetimes.
    Handles both naive and aware datetimes by converting to aware.
    
    Args:
        start: Start datetime (naive or aware)
        end: End datetime (naive or aware)
        
    Returns:
        Duration in seconds (integer)
    """
    # Make sure both are timezone-aware
    start_aware = make_aware(start)
    end_aware = make_aware(end)
    
    # Calculate duration
    duration = (end_aware - start_aware).total_seconds()
    return int(duration)


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Examples:
        65 -> "1m 5s"
        3665 -> "1h 1m 5s"
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)