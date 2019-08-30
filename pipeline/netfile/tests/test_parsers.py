import datetime
import os
from decimal import Decimal
from uuid import UUID

import pytest

from ..models import (
    Form700Filing, Office, ScheduleA1, ScheduleA2, ScheduleB, ScheduleC1, ScheduleC2, ScheduleD, ScheduleDGift
)
from ..parsers import parse_filing
from ..utils import TIMEZONE


def read_filing(filing_id: str):
    file_path = os.path.join(os.path.dirname(__file__), 'fixtures', f'{filing_id}.xml')

    with open(file_path, 'r') as test_file:
        raw_xml = test_file.read()

    return raw_xml


def _parse_filing(filing_id: str):
    raw_xml = read_filing(filing_id)
    parse_filing(filing_id, raw_xml)
    filings = Form700Filing.select()
    assert len(filings) == 1

    filing = filings[0]
    assert filing.id == filing_id

    return filing


@pytest.mark.usefixtures("reset_database")
def test_parse_filing():
    filing = _parse_filing('182305528')
    assert filing.first_name == 'Desley'
    assert filing.last_name == 'Brooks'
    assert filing.get().date_signed == datetime.datetime(2019, 8, 13, 0, 20, 48)

    offices = Office.select()
    assert (len(offices)) == 1

    assert offices[0] == Office(
        id=UUID('97574a2f-3303-4680-b96b-6266c7d88804'),
        filing=filing,
        agency='City of Oakland',
        division_board_district='00611 - District Six Unit',
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


@pytest.mark.usefixtures("reset_database")
def test_parse_filing_duplicates():
    for filing_id in ('177199734', '177199959',):
        raw_xml = read_filing(filing_id)
        parse_filing(filing_id, raw_xml)


@pytest.mark.usefixtures("reset_database")
def test_parse_schedule_a2():
    filing = _parse_filing('178665313')

    schedule_a2_attachments = ScheduleA2.select()
    assert len(schedule_a2_attachments) == 1

    assert schedule_a2_attachments[0] == ScheduleA2(
        id=UUID('831903c6-3d3a-48bf-b22f-8b5c907c60cf'),
        filing=filing,
        address_city='Oakland',
        address_state='CA',
        address_zip='94619',
        date_acquired=None,
        date_disposed=None,
        description='real Estate investment',
        business_position='owner',
        entity_name='JOseph & Mary Tanios',
        fair_market_value='100001-1000000',
        gross_income_received='10001-100000',
        nature_of_investment='sole_proprietorship',
        nature_of_investment_other_description=None
    )


@pytest.mark.usefixtures("reset_database")
def test_parse_schedule_b():
    filing = _parse_filing('178665313')

    schedule_b_attachments = ScheduleB.select()
    assert len(schedule_b_attachments) == 2

    assert schedule_b_attachments[0] == ScheduleB(
        id=UUID('befc368a-2c3c-43da-a2a8-50e940ab78c4'),
        filing=filing,
        city='Oakland , Ca 94608',
        date_acquired=None,
        date_disposed=None,
        fair_market_value='100001-1000000',
        gross_income_received='10001-100000',
        nature_of_interest='ownership',
        parcel_or_address='865 29th street',
    )
    assert schedule_b_attachments[1] == ScheduleB(
        id=UUID('b069b6b3-3fde-4e66-95b9-a3eef4615111'),
        filing=filing,
        city='Oakland, CA 94605',
        date_acquired=None,
        date_disposed=None,
        fair_market_value='100001-1000000',
        gross_income_received='1001-10000',
        nature_of_interest='ownership',
        parcel_or_address='865 29th Street',
    )


@pytest.mark.usefixtures("reset_database")
def test_parse_schedule_c1():
    filing = _parse_filing('178665313')

    schedule_c1_attachments = ScheduleC1.select()
    assert len(schedule_c1_attachments) == 2

    assert schedule_c1_attachments[0] == ScheduleC1(
        id=UUID('dea22ddc-4d42-4863-ac0b-681470f5219c'),
        filing=filing,
        address_city='Oakland',
        address_state='Ca',
        address_zip='94612',
        business_activity='Real property',
        business_position='Owner',
        gross_income_received='10001-100000',
        name_of_income_source='Rental property',
        reason_for_income='rental_income',
    )
    assert schedule_c1_attachments[1] == ScheduleC1(
        id=UUID('c7a60ac2-4f93-4d07-b409-61c5b23faabc'),
        filing=filing,
        address_city='Oakland',
        address_state='CA',
        address_zip='94612',
        business_activity='865, 29th Street',
        business_position='Real Property',
        gross_income_received='10001-100000',
        name_of_income_source='Rental Property',
        reason_for_income='rental_income',
    )


@pytest.mark.usefixtures("reset_database")
def test_parse_schedule_c2():
    filing = _parse_filing('178665313')

    schedule_c2_attachments = ScheduleC2.select()
    assert len(schedule_c2_attachments) == 1

    assert schedule_c2_attachments[0] == ScheduleC2(
        id=UUID('0edb096b-b390-4629-9afe-2393ac5fc1f0'),
        filing=filing,
        address_city='Irving',
        address_state='TX',
        address_zip='75063',
        business_activity='Mr. Cooper 4000 Horison Way Irving, Texas 75063',
        has_interest_rate=True,
        highest_balance='100000+',
        interest_rate=Decimal('4.8'),
        loan_security='none',
        name_of_lender='Mr. Cooper 4000 Horison Way Irving, Texas 75063',
        term=360,
        term_type='month'
    )


@pytest.mark.usefixtures("reset_database")
def test_parse_schedule_d():
    filing = _parse_filing('178032623')

    schedule_d_attachments = ScheduleD.select()
    assert len(schedule_d_attachments) == 1

    attachment = schedule_d_attachments[0]
    assert attachment == ScheduleD(
        id=UUID('4ac70b1f-405d-4a09-b7bd-2ff4c7a1be71'),
        filing=filing,
        address_city='Oakland',
        address_state='CA',
        address_zip='94607',
        business_activity=None,
        name_of_source='Warriors Community Foundation',
    )

    assert len(attachment.gifts) == 1

    assert attachment.gifts[0] == ScheduleDGift(
        id=UUID('4c5a26b8-27df-49f3-81a8-109818bb7aee'),
        schedule=attachment,
        amount=Decimal('100.00'),
        description='Ticket to Game',
        gift_date=TIMEZONE.localize(datetime.datetime(2018, 2, 22, 0, 0, 0)).timestamp(),
    )
