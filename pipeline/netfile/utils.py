from typing import Optional, Sequence

import pytz
from dateutil.parser import parse

TIMEZONE = pytz.timezone('America/Los_Angeles')


def clean_boolean(s: Optional[str]) -> bool:
    """ Converts the string to a boolean. """
    s = s or ''
    s = s.lower()
    return s in ('true', '1')


def clean_datetime(s: Optional[str]) -> Optional[int]:
    """ Converts a given string to a UTC timestamp.

    Note:
        All inputs are assumed to be in the America/Los Angeles timezone,
        and are converted to UTC after being parsed.
    """
    if not s:
        return None

    try:
        dt = parse(s)
        dt = TIMEZONE.localize(dt)
        dt = dt.astimezone(pytz.utc)
        return int(dt.timestamp())
    except ValueError:
        return None


def clean_choice(s: Optional[str], choices: Sequence[str]) -> Optional[str]:
    if not s or s == '0':
        return None

    return choices[int(s) - 1]


def clean_string(s: Optional[str]) -> Optional[str]:
    return s.strip() if s else None
