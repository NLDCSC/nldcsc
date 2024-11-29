from datetime import datetime


def timestamp_to_strf_string(timestamp: int) -> str:
    """
    Method that will take the provided timestamp and converts it into a RFC3339 date time string

    Args:
        timestamp: unix timestamp

    Returns:
        Date time string
    """
    value = datetime.utcfromtimestamp(timestamp)

    return value.strftime("%Y-%m-%d %H:%M:%S")
