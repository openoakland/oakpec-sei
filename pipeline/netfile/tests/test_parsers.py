import datetime
import os
from uuid import UUID

import pytest

from ..models import Form700Filing, Office, ScheduleA1
from ..parsers import parse_filing


@pytest.mark.usefixtures("reset_database")
def test_parse_filing():
    filing_id = '182305528'
    raw_xml = read_filing(filing_id)
    parse_filing(filing_id, raw_xml)

    filings = Form700Filing.select()
    assert len(filings) == 1

    filing = filings[0]
    assert filing.id == filing_id
    assert filing.first_name == 'Desley'
    assert filing.last_name == 'Brooks'
    assert filing.get().date_signed == datetime.datetime(2019, 8, 13, 0, 20, 48)

    offices = Office.select()
    assert (len(offices)) == 1

    assert offices[0] == Office(
        id=UUID('97574a2f-3303-4680-b96b-6266c7d88804'),
        filing=filing,
        agency='City of Oakland',
        division_board_district='00611  - District Six Unit',
        is_primary=True,
        position='Council Member',
        election_date=None,
        assuming_date=None,
        leaving_date=None,
    )

    schedule_a1_attachments = ScheduleA1.select()
    assert len(schedule_a1_attachments) == 6

    assert schedule_a1_attachments[0] == ScheduleA1(
        id=UUID('2fcdab47-276c-477a-82cc-5dcbeb1e8bf8'),
        filing=filing,
        date_acquired=None,
        date_disposed=None,
        description='Equipment and Technologies',
        name_of_business_entity='Applied Materials',
        fair_market_value='2000-10000',
        nature_of_investment='stock',
        nature_of_investment_other_description=None,
        partnership_amount=None
    )
    assert schedule_a1_attachments[3] == ScheduleA1(
        id=UUID('cc56f9e3-35bc-49f8-9b77-c50c0c8045c4'),
        filing=filing,
        date_acquired=None,
        date_disposed=None,
        description='Retail',
        name_of_business_entity='Costco',
        fair_market_value='10001-100000',
        nature_of_investment='stock',
        nature_of_investment_other_description=None,
        partnership_amount=None
    )


def read_filing(filing_id):
    file_path = os.path.join(os.path.dirname(__file__), 'fixtures', f'{filing_id}.xml')
    with open(file_path, 'r') as test_file:
        raw_xml = test_file.read()
    return raw_xml


@pytest.mark.usefixtures("reset_database")
def test_parse_filing_duplicates():
    for filing_id in ('177199734', '177199959',):
        raw_xml = read_filing(filing_id)
        parse_filing(filing_id, raw_xml)
