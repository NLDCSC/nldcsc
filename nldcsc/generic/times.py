import calendar
from datetime import datetime


ISOFORMAT = "%Y-%m-%dT%H:%M:%SZ"


def timestringTOtimestamp(timestring):
    """
    Method to convert a given date time string into a timestamp. Timestring is matched to the date_time_formats
    'date time string formats' list. If matched will return a timestamp integer; will return False otherwise.

    :param timestring: date time string
    :type timestring: str
    :return: unix timestamp
    :rtype: int
    """

    date_time_formats = [
        "%d-%m-%Y",
        "%d-%m-%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%H:%M:%S %d-%m-%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S,%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S,%fZ",
        "%Y-%m-%dT%H:%M:%S.%fZ%z",
        "%Y-%m-%dT%H:%M:%S,%fZ%z",
        "%Y-%m-%d %H:%M:%S.%f%z",
    ]
    match = False

    # try to match string formats to given string
    for each in date_time_formats:
        try:
            match = datetime.strptime(timestring, each)
        except ValueError:
            continue

    if match:
        match = calendar.timegm(match.utctimetuple())

    return match


def datetimeTOtimestamp(date_time_object):
    return calendar.timegm(date_time_object.utctimetuple())


def dateTOtimestamp(date_time_object):
    return calendar.timegm(date_time_object.timetuple())


def timestampTOdatetime(timestamp):
    """
    Method that will take the provided timestamp and converts it into a date time object

    :param timestamp: unix timestamp
    :type timestamp: int
    :return: date time object
    :rtype: datetime
    """
    value = datetime.utcfromtimestamp(timestamp)

    return value


def timestampTOdatestring(timestamp):
    """
    Method that will take the provided timestamp and converts it into a date time string

    :param timestamp: unix timestamp
    :type timestamp: int
    :return: date time object
    :rtype: datetime.datetime (format: '%d-%m-%Y')
    """
    value = datetime.utcfromtimestamp(timestamp)

    return value.strftime("%d-%m-%Y")


def timestampTOdatetimestring(timestamp, vis=False):
    """
    Method that will take the provided timestamp and converts it into a RFC3339 date time string

    :param timestamp: unix timestamp
    :type timestamp: int
    :return: date time object
    :rtype: datetime.datetime (format: '%d-%m-%YT%H:%M:%SZ')
    """
    value = datetime.utcfromtimestamp(timestamp)

    if not vis:
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        return value.strftime("%Y-%m-%d %H:%M:%S")


def timestampTOcalendarattrs(timestamp):
    value = datetime.utcfromtimestamp(timestamp)

    day = value.strftime("%d")
    month = value.strftime("%B")
    weekday = value.strftime("%A")

    return {"day": day, "month": month, "weekday": weekday}


def timestringTOdatetimestring(timestring):
    timestamp = timestringTOtimestamp(timestring=timestring)

    if timestamp is False:
        return False

    return timestampTOdatetimestring(timestamp=timestamp)
