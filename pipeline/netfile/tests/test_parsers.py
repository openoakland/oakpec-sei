import datetime
import os
from decimal import Decimal
from uuid import UUID

import pytest

from ..models import (
    Form700Filing, Office, ScheduleA1, ScheduleA2, ScheduleB, ScheduleBIncomeSource, ScheduleC1, ScheduleC2, ScheduleD,
    ScheduleDGift, ScheduleE
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
    return Form700Filing.get_by_id(filing_id)


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
def test_parse_filing_amendments():
    filing = _parse_filing('177692551')
    amendment = _parse_filing('181517263')

    assert amendment.amends == filing


@pytest.mark.usefixtures("reset_database")
def test_parse_filing_comments_schedule_b():
    filing = _parse_filing('178774422')
    assert filing.comments_schedule_b == 'Spouse is owner'


@pytest.mark.usefixtures("reset_database")
def test_parse_filing_comments_schedule_d():
    filing = _parse_filing('178768108')
    assert filing.comments_schedule_d == 'I think there are a few things missing from this list that I do not have ' \
                                         'record of at the moment of filing.'


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
def test_parse_schedule_b_income_sources():
    _parse_filing('178069526')

    schedule_b_attachments = ScheduleB.select()
    assert len(schedule_b_attachments) == 2

    schedule = schedule_b_attachments[1]
    income_sources = schedule.income_sources
    assert len(income_sources) == 2

    assert income_sources[0] == ScheduleBIncomeSource(
        id=UUID('826f6f85-21ca-4a57-9884-751e21f88dcf'),
        schedule=schedule,
        name='Name(s) redacted'
    )
    assert income_sources[1] == ScheduleBIncomeSource(
        id=UUID('4cc13eeb-7232-489f-b00f-d9edaba4aec2'),
        schedule=schedule,
        name=''
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
    filing = _parse_filing('177423011')

    schedule_c2_attachments = ScheduleC2.select()
    assert len(schedule_c2_attachments) == 2

    assert schedule_c2_attachments[0] == ScheduleC2(
        id=UUID('d48e2404-38a0-4a5c-aa15-16b556027f0c'),
        filing=filing,
        address_city='walnut creek',
        address_state='ca',
        address_zip='94596',
        business_activity=None,
        has_interest_rate=True,
        highest_balance='100000+',
        interest_rate=Decimal('3.25'),
        interest_rate_raw='3.25',
        loan_security='real_property',
        loan_security_real_property_address_city='castro valley',
        loan_security_real_property_address_state='ca',
        loan_security_real_property_address_zip='94552',
        name_of_lender='Chase',
        term=10,
        term_type='year'
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


@pytest.mark.usefixtures("reset_database")
def test_parse_schedule_e():
    filing = _parse_filing('178032623')

    schedule_e_attachments = ScheduleE.select()
    assert len(schedule_e_attachments) == 3

    assert schedule_e_attachments[0] == ScheduleE(
        id=UUID('a5723c51-4826-4813-9b98-b43d61af8ad8'),
        filing=filing,
        address_city='Washington',
        address_state='DC',
        address_zip='20001',
        amount=Decimal(0),
        business_activity='Travel and Lodging for Conference',
        end_date=TIMEZONE.localize(datetime.datetime(2018, 9, 26, 0, 0, 0)).timestamp(),
        is_nonprofit=False,
        is_other=True,
        made_speech=False,
        name_of_source='National League of Cities',
        other_description='Participated in Conference',
        start_date=TIMEZONE.localize(datetime.datetime(2018, 9, 23, 0, 0, 0)).timestamp(),
        travel_description='New Orleans, Louisiana',
        type_of_payment='gift',
    )
    assert schedule_e_attachments[1] == ScheduleE(
        id=UUID('0db54b8d-772b-4e71-a83e-0f2d43a7f5e6'),
        filing=filing,
        address_city='Cambridge',
        address_state='MA',
        address_zip='02138',
        amount=Decimal(0),
        business_activity='Travel and Lodging for Conference',
        end_date=TIMEZONE.localize(datetime.datetime(2018, 10, 10, 0, 0, 0)).timestamp(),
        is_nonprofit=True,
        is_other=True,
        made_speech=False,
        name_of_source='Harvard Graduate School of Education',
        other_description='Participated in Conference',
        start_date=TIMEZONE.localize(datetime.datetime(2018, 10, 8, 0, 0, 0)).timestamp(),
        travel_description='Cambridge, MA',
        type_of_payment='gift',
    )
    assert schedule_e_attachments[2] == ScheduleE(
        id=UUID('e92e519c-9ad1-4dac-8d80-295ae2040ace'),
        filing=filing,
        address_city='Cambridge',
        address_state='MA',
        address_zip='02138',
        amount=Decimal(0),
        business_activity='Travel and Lodging for Conference',
        end_date=TIMEZONE.localize(datetime.datetime(2018, 11, 30, 0, 0, 0)).timestamp(),
        is_nonprofit=True,
        is_other=True,
        made_speech=False,
        name_of_source='Harvard Graduate School of Education',
        other_description='Participated in Conference',
        start_date=TIMEZONE.localize(datetime.datetime(2018, 11, 25, 0, 0, 0)).timestamp(),
        travel_description='Cambridge, MA',
        type_of_payment='gift',
    )
