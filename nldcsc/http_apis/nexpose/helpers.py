from typing import Any

from .objects import NexposeFilter, NexposeFilterOperator


def filter_from_args(
    field: str,
    operator: NexposeFilterOperator,
    value: Any = None,
    upper: Any = None,
    lower: Any = None,
) -> NexposeFilter:
    if value is None and (upper is None or lower is None):
        raise ValueError("value, upper or lower required")

    filter = {"field": field, "operator": operator}

    if value:
        filter["value"] = value

    if upper and lower:
        filter["upper"] = upper
        filter["lower"] = lower

    return filter
