import datetime
import decimal

import pytz

from ..utils import TIMEZONE, clean_boolean, clean_datetime, clean_decimal, clean_integer, clean_string


def test_clean_string():
    assert clean_string('a ') == 'a'
    assert clean_string('') == ''
    assert clean_string(None) is None
    assert clean_string('a\nb') == 'a b'
    assert clean_string('a\n\nb') == 'a b'


def test_clean_boolean():
    data = {
        'True': True,
        'TRUE': True,
        'true': True,
        '1': True,
        'False': False,
        'FALSE': False,
        'false': False,
        '0': False,
    }

    for dirty, expected in data.items():
        assert clean_boolean(dirty) == expected, f'Invalid output for {dirty}'


def test_clean_datetime():
    data = {
        '1/12/2018 8:14:01 AM': datetime.datetime(2018, 1, 12, 8, 14, 1),
        '11/9/2018': datetime.datetime(2018, 11, 9),
        '2016-09-22 15:51:13-07:00': datetime.datetime(2016, 9, 22, 15, 51, 13),
        '2018-11-09 00:00:00-08:00': datetime.datetime(2018, 11, 9),
    }

    for dirty, expected in data.items():
        expected = TIMEZONE.localize(expected)
        expected = expected.astimezone(pytz.utc)
        expected = expected.timestamp()
        assert clean_datetime(dirty) == expected, dirty

    assert clean_datetime('') is None


def test_clean_decimal():
    assert clean_decimal('') is None
    assert clean_decimal('100') == decimal.Decimal(100)


def test_clean_integer():
    assert clean_integer('') is None
    assert clean_integer(None) is None
    assert clean_integer('3') == 3
