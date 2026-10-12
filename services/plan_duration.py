"""Parsing and display helpers for subscription durations."""

import re


_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٫", "0123456789.")
_DURATION_PATTERN = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(ماه|month|months|ساعت|hour|hours|h)?\s*$",
    re.IGNORECASE,
)


def parse_duration(value: str) -> tuple[float, str]:
    """Parse values such as ``0.01 ماه`` and ``24 ساعت``.

    Values without a unit retain the original behaviour and are treated as
    months, so entering ``1`` still means one month.
    """
    normalized = value.translate(_PERSIAN_DIGITS).strip().lower()
    match = _DURATION_PATTERN.fullmatch(normalized)
    if match is None:
        raise ValueError("invalid duration")

    amount = float(match.group(1))
    if amount <= 0:
        raise ValueError("duration must be positive")

    unit = match.group(2)
    return amount, "hour" if unit in {"ساعت", "hour", "hours", "h"} else "month"


def format_duration(amount: float, unit: str) -> str:
    amount_text = f"{amount:g}"
    return f"{amount_text} {'ساعت' if unit == 'hour' else 'ماه'}"
