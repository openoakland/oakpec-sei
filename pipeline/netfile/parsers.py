import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Optional, Tuple
from uuid import UUID

from .models import (
    BaseModel, Form700Filing, Office, ScheduleA1, ScheduleA2, ScheduleB, ScheduleBIncomeSource, ScheduleC1, ScheduleC2,
    ScheduleD, ScheduleDGift, ScheduleE, db
)
from .utils import clean_boolean, clean_choice, clean_datetime, clean_decimal, clean_integer, clean_string

logger = logging.getLogger(__name__)


def find_and_clean_text(element: ET.Element, path: str) -> Optional[str]:
    return clean_string(element.findtext(path))


def _parse_comments(filing: Form700Filing, xml_tree: ET.Element) -> Form700Filing:
    filing.comments_schedule_a1 = find_and_clean_text(xml_tree, 'comments_schedule_a1')
    filing.comments_schedule_a2 = find_and_clean_text(xml_tree, 'comments_schedule_a2')
    filing.comments_schedule_b = find_and_clean_text(xml_tree, 'comments_schedule_b')
    filing.comments_schedule_c = find_and_clean_text(xml_tree, 'comments_schedule_c')
    filing.comments_schedule_d = find_and_clean_text(xml_tree, 'comments_schedule_d')
    filing.comments_schedule_e = find_and_clean_text(xml_tree, 'comments_schedule_e')
    return filing


def _parse_cover(filing: Form700Filing, xml_tree: ET.Element) -> Form700Filing:
    filing.filer_id = find_and_clean_text(xml_tree, 'filing_information/filer_id')
    report_year = find_and_clean_text(xml_tree, 'report_year')
    assert report_year
    filing.report_year = int(report_year)

    # NOTE: This is a small hack. `amends` is a foreign key, but peewee allows the ID to be set rather than
    # the related instance.
    filing.amends = find_and_clean_text(xml_tree, 'filing_information/amendment_superceded_filing_id')

    cover = xml_tree.find('cover')
    assert isinstance(cover, ET.Element)
    filing.first_name = find_and_clean_text(cover, 'first_name')
    filing.last_name = find_and_clean_text(cover, 'last_name')
    filing.date_signed = clean_datetime(find_and_clean_text(cover, 'verification/date_signed'))

    return filing


def _parse_offices(filing: Form700Filing, xml_tree: ET.Element) -> List[Office]:
    office_elements = xml_tree.findall('cover/offices/office')
    offices = []
    for element in office_elements:
        office_id = UUID(find_and_clean_text(element, 'id'))
        office = Office.get_or_none(Office.id == office_id)
        if not office:
            office = Office(
                id=office_id,
                filing=filing,
                agency=find_and_clean_text(element, 'agency'),
                division_board_district=find_and_clean_text(element, 'division_board_district'),
                position=find_and_clean_text(element, 'position'),
                is_primary=clean_boolean(find_and_clean_text(element, 'is_primary')),
                election_date=clean_datetime(find_and_clean_text(element, 'election_date')),
                assuming_date=clean_datetime(find_and_clean_text(element, 'assuming_date')),
                leaving_date=clean_datetime(find_and_clean_text(element, 'leaving_date')),
            )
            offices.append(office)
    return offices


def _parse_schedule_a1_attachments(filing: Form700Filing, xml_tree: ET.Element) -> List[ScheduleA1]:
    attachments = []
    elements = xml_tree.findall('schedule_a_1s/schedule_a_1')
    for element in elements:
        attachment = ScheduleA1(
            id=UUID(find_and_clean_text(element, 'id')),
            filing=filing,
            date_acquired=clean_datetime(find_and_clean_text(element, 'date_acquired')),
            date_disposed=clean_datetime(find_and_clean_text(element, 'date_disposed')),
            description=find_and_clean_text(element, 'description'),
            name_of_business_entity=find_and_clean_text(element, 'name_of_business_entity'),
            fair_market_value=clean_choice(
                find_and_clean_text(element, 'fair_market_value'),
                ScheduleA1.fair_market_value_choices
            ),
            nature_of_investment=clean_choice(
                find_and_clean_text(element, 'nature_of_investment'),
                ScheduleA1.nature_of_investment_choices
            ),
            nature_of_investment_other_description=find_and_clean_text(element,
                                                                       'nature_of_investment_other_description'),
            partnership_amount=clean_choice(
                find_and_clean_text(element, 'partnership_amount'),
                ScheduleA1.partnership_amount_choices
            ),
        )
        attachments.append(attachment)

    return attachments


def _parse_schedule_a2_attachments(filing: Form700Filing, xml_tree: ET.Element) -> List[ScheduleA2]:
    attachments = []
    elements = xml_tree.findall('schedule_a_2s/schedule_a_2')
    for element in elements:
        attachment = ScheduleA2(
            id=UUID(find_and_clean_text(element, 'id')),
            filing=filing,
            address_city=find_and_clean_text(element, 'address/city'),
            address_state=find_and_clean_text(element, 'address/state'),
            address_zip=find_and_clean_text(element, 'address/zip'),
            business_position=find_and_clean_text(element, 'business_position'),
            date_acquired=clean_datetime(find_and_clean_text(element, 'date_acquired')),
            date_disposed=clean_datetime(find_and_clean_text(element, 'date_disposed')),
            description=find_and_clean_text(element, 'description'),
            entity_name=find_and_clean_text(element, 'entity_name'),
            fair_market_value=clean_choice(
                find_and_clean_text(element, 'fair_market_value_schedule_a_2'),
                ScheduleA2.fair_market_value_choices
            ),
            gross_income_received=clean_choice(
                find_and_clean_text(element, 'gross_income_received'),
                ScheduleA2.gross_income_received_choices
            ),
            nature_of_investment=clean_choice(
                find_and_clean_text(element, 'nature_of_investment'),
                ScheduleA2.nature_of_investment_choices
            ),
            nature_of_investment_other_description=find_and_clean_text(element,
                                                                       'nature_of_investment_other_description'),
        )
        attachments.append(attachment)

    return attachments


def _parse_schedule_b_attachments(filing: Form700Filing, xml_tree: ET.Element) -> \
        Tuple[List[ScheduleB], List[ScheduleBIncomeSource]]:
    attachments = []
    income_sources = []
    elements = xml_tree.findall('schedule_bs/schedule_b')
    for element in elements:
        attachment = ScheduleB(
            id=UUID(find_and_clean_text(element, 'id')),
            filing=filing,
            city=find_and_clean_text(element, 'city'),
            date_acquired=clean_datetime(find_and_clean_text(element, 'date_acquired')),
            date_disposed=clean_datetime(find_and_clean_text(element, 'date_disposed')),
            fair_market_value=clean_choice(
                find_and_clean_text(element, 'fair_market_value'),
                ScheduleB.fair_market_value_choices
            ),
            gross_income_received=clean_choice(
                find_and_clean_text(element, 'gross_income_received'),
                ScheduleB.gross_income_received_choices
            ),
            nature_of_interest=clean_choice(
                find_and_clean_text(element, 'nature_of_interest'),
                ScheduleB.nature_of_interest_choices
            ),
            parcel_or_address=find_and_clean_text(element, 'parcel_or_address'),
        )
        attachments.append(attachment)

        for income_source_element in element.findall('income_sources/source'):
            income_source = ScheduleBIncomeSource(
                id=UUID(find_and_clean_text(income_source_element, 'id')),
                schedule=attachment,
                name=find_and_clean_text(income_source_element, 'name'),
            )
            income_sources.append(income_source)

    return attachments, income_sources


def _parse_schedule_c1_attachments(filing: Form700Filing, xml_tree: ET.Element) -> List[ScheduleA2]:
    attachments = []
    elements = xml_tree.findall('schedule_c_1s/schedule_c_1')
    for element in elements:
        attachment = ScheduleC1(
            id=UUID(find_and_clean_text(element, 'id')),
            filing=filing,
            address_city=find_and_clean_text(element, 'address/city'),
            address_state=find_and_clean_text(element, 'address/state'),
            address_zip=find_and_clean_text(element, 'address/zip'),
            business_activity=find_and_clean_text(element, 'business_activity'),
            business_position=find_and_clean_text(element, 'business_position'),
            gross_income_received=clean_choice(
                find_and_clean_text(element, 'gross_income_received_schedule_c_1'),
                ScheduleC1.gross_income_received_choices
            ),
            name_of_income_source=find_and_clean_text(element, 'name_of_income_source'),
            reason_for_income=clean_choice(
                find_and_clean_text(element, 'reason_for_income'),
                ScheduleC1.reason_for_income_choices
            ),
            reason_for_income_other=find_and_clean_text(element, 'reason_for_income_other'),
        )
        attachments.append(attachment)

    return attachments


def _parse_schedule_c2_attachments(filing: Form700Filing, xml_tree: ET.Element) -> List[ScheduleA2]:
    attachments = []
    elements = xml_tree.findall('schedule_c_2s/schedule_c_2')
    for element in elements:

        term_type = find_and_clean_text(element, 'loan/term_type')
        if term_type:
            term_type = term_type.lower()

        interest_rate = None
        raw_interest_rate = find_and_clean_text(element, 'loan/interest_rate')
        if raw_interest_rate:
            match = re.match(r'([\d\.]+)', raw_interest_rate)
            assert match
            raw_interest_rate = match[1]
            interest_rate = clean_decimal(clean_string(raw_interest_rate))

        property_address_element = element.find('loan_security_real_property_address')
        assert property_address_element is not None, \
            f'loan_security_real_property_address element is missing from filing {filing.id}'

        attachment = ScheduleC2(
            id=UUID(find_and_clean_text(element, 'id')),
            filing=filing,
            address_city=find_and_clean_text(element, 'loan/address/city'),
            address_state=find_and_clean_text(element, 'loan/address/state'),
            address_zip=find_and_clean_text(element, 'loan/address/zip'),
            business_activity=find_and_clean_text(element, 'loan/business_activity'),
            has_interest_rate=not clean_boolean(find_and_clean_text(element, 'loan/has_no_interest_rate')),
            highest_balance=clean_choice(
                find_and_clean_text(element, 'loan/highest_balance'),
                ScheduleC2.highest_balance_choices
            ),
            interest_rate=interest_rate,
            interest_rate_raw=find_and_clean_text(element, 'loan/interest_rate'),
            loan_security=clean_choice(
                find_and_clean_text(element, 'loan_security'),
                ScheduleC2.loan_security_choices
            ),
            loan_security_real_property_address_city=find_and_clean_text(property_address_element, 'city'),
            loan_security_real_property_address_state=find_and_clean_text(property_address_element, 'state'),
            loan_security_real_property_address_zip=find_and_clean_text(property_address_element, 'zip'),
            name_of_lender=find_and_clean_text(element, 'loan/name_of_lender'),
            term=clean_integer(find_and_clean_text(element, 'loan/term')),
            term_type=term_type,
        )
        attachments.append(attachment)

    return attachments


def _parse_schedule_d_attachments(filing: Form700Filing, xml_tree: ET.Element) -> \
        Tuple[List[ScheduleD], List[ScheduleDGift]]:
    attachments = []
    gifts = []
    elements = xml_tree.findall('schedule_ds/schedule_d')
    for schedule_element in elements:
        attachment = ScheduleD(
            id=UUID(find_and_clean_text(schedule_element, 'id')),
            filing=filing,
            address_city=find_and_clean_text(schedule_element, 'address/city'),
            address_state=find_and_clean_text(schedule_element, 'address/state'),
            address_zip=find_and_clean_text(schedule_element, 'address/zip'),
            business_activity=find_and_clean_text(schedule_element, 'business_activity'),
            name_of_source=find_and_clean_text(schedule_element, 'name_of_source'),
        )
        attachments.append(attachment)

        gift_elements = schedule_element.findall('gifts/gift')
        for gift_element in gift_elements:
            gift = ScheduleDGift(
                id=UUID(find_and_clean_text(gift_element, 'id')),
                schedule=attachment,
                amount=clean_decimal(find_and_clean_text(gift_element, 'amount')),
                description=find_and_clean_text(gift_element, 'description'),
                gift_date=clean_datetime(find_and_clean_text(gift_element, 'gift_date')),
            )
            gifts.append(gift)

    return attachments, gifts


def _parse_schedule_e_attachments(filing: Form700Filing, xml_tree: ET.Element) -> List[ScheduleE]:
    attachments = []
    elements = xml_tree.findall('schedule_es/schedule_e')
    for element in elements:
        attachment = ScheduleE(
            id=UUID(find_and_clean_text(element, 'id')),
            filing=filing,
            address_city=find_and_clean_text(element, 'address/city'),
            address_state=find_and_clean_text(element, 'address/state'),
            address_zip=find_and_clean_text(element, 'address/zip'),
            amount=clean_decimal(find_and_clean_text(element, 'amount')),
            business_activity=find_and_clean_text(element, 'business_activity'),
            end_date=clean_datetime(find_and_clean_text(element, 'end_date')),
            is_nonprofit=clean_boolean(find_and_clean_text(element, 'is_nonprofit')),
            is_other=clean_boolean(find_and_clean_text(element, 'is_other')),
            made_speech=clean_boolean(find_and_clean_text(element, 'made_speech')),
            name_of_source=find_and_clean_text(element, 'name_of_source'),
            other_description=find_and_clean_text(element, 'other_description'),
            start_date=clean_datetime(find_and_clean_text(element, 'start_date')),
            travel_description=find_and_clean_text(element, 'travel_description'),
            type_of_payment=clean_choice(
                find_and_clean_text(element, 'type_of_payment'),
                ScheduleE.type_of_payment_choices
            ),
        )
        attachments.append(attachment)

    return attachments


def _save_models(instances: List[BaseModel]) -> None:
    for instance in instances:
        instance.save(force_insert=True)


def parse_filing(filing_id: str, raw_data: str) -> Form700Filing:
    logger.info(f'Parsing Form 700 filing {filing_id}')
    xml_tree = ET.fromstring(raw_data)
    filing = Form700Filing(id=filing_id)

    with db.atomic() as transaction:
        try:
            filing = _parse_cover(filing, xml_tree)
            filing = _parse_comments(filing, xml_tree)
            offices = _parse_offices(filing, xml_tree)
            schedule_a1_attachments = _parse_schedule_a1_attachments(filing, xml_tree)
            schedule_a2_attachments = _parse_schedule_a2_attachments(filing, xml_tree)
            schedule_b_attachments, schedule_b_income_sources = _parse_schedule_b_attachments(filing, xml_tree)
            schedule_c1_attachments = _parse_schedule_c1_attachments(filing, xml_tree)
            schedule_c2_attachments = _parse_schedule_c2_attachments(filing, xml_tree)
            schedule_d_attachments, schedule_d_gifts = _parse_schedule_d_attachments(filing, xml_tree)
            schedule_e_attachments = _parse_schedule_e_attachments(filing, xml_tree)
            _save_models([filing])
            _save_models(offices)
            _save_models(schedule_a1_attachments)
            _save_models(schedule_a2_attachments)
            _save_models(schedule_b_attachments)
            _save_models(schedule_b_income_sources)
            _save_models(schedule_c1_attachments)
            _save_models(schedule_c2_attachments)
            _save_models(schedule_d_attachments)
            _save_models(schedule_d_gifts)
            _save_models(schedule_e_attachments)
        except Exception:  # pylint: disable=broad-except
            transaction.rollback()
            logger.exception(f'Failed to parse filing {filing_id}!')

    logger.info(f'Successfully parsed Form 700 filing {filing_id}')
    return filing
