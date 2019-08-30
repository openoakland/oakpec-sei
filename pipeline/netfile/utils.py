import decimal
import logging
import re
from typing import Optional, Sequence

import pytz
from dateutil.parser import parse

logger = logging.getLogger(__name__)

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
        if dt.tzinfo is None:
            dt = TIMEZONE.localize(dt)
        dt = dt.astimezone(pytz.utc)
        return int(dt.timestamp())
    except ValueError:
        logger.exception('Failed to clean datetime: %s', s)
        return None


def clean_choice(s: Optional[str], choices: Sequence[str]) -> Optional[str]:
    if not s or s == '0':
        return None

    return choices[int(s) - 1]


def clean_decimal(s: Optional[str]) -> Optional[decimal.Decimal]:
    return decimal.Decimal(s) if s else None


def clean_string(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None

    return re.sub(r'\s+', ' ', s).strip()


def clean_integer(s: Optional[str]) -> Optional[int]:
    if s is None:
        return None

    try:
        return int(s)
    except ValueError:
        logger.exception('Failed to clean integer: %s', s)
        return None
