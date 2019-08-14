import logging
import xml.etree.ElementTree as ET
from typing import List, Optional
from uuid import UUID

from .models import BaseModel, Form700Filing, Office, ScheduleA1, db
from .utils import clean_boolean, clean_choice, clean_datetime

logger = logging.getLogger(__name__)


def _get_node_value(root: ET.Element, path: str) -> Optional[str]:
    return root.findtext(path)


def _parse_cover(filing: Form700Filing, xml_tree: ET.Element) -> Form700Filing:
    filing.filer_id = xml_tree.findtext('filing_information/filer_id')
    report_year = xml_tree.findtext('report_year')
    assert report_year
    filing.report_year = int(report_year)

    cover = xml_tree.find('cover')
    assert isinstance(cover, ET.Element)
    filing.first_name = cover.findtext('first_name')
    filing.last_name = cover.findtext('last_name')
    filing.date_signed = clean_datetime(cover.findtext('verification/date_signed'))

    return filing


def _parse_offices(filing: Form700Filing, xml_tree: ET.Element) -> List[Office]:
    office_elements = xml_tree.findall('cover/offices/office')
    offices = []
    for element in office_elements:
        office = Office(
            id=UUID(element.findtext('id')),
            filing=filing,
            agency=element.findtext('agency'),
            division_board_district=element.findtext('division_board_district'),
            position=element.findtext('position'),
            is_primary=clean_boolean(element.findtext('is_primary')),
            election_date=clean_datetime(element.findtext('election_date')),
            assuming_date=clean_datetime(element.findtext('assuming_date')),
            leaving_date=clean_datetime(element.findtext('leaving_date')),
        )
        offices.append(office)
    return offices


def _parse_schedule_a1_attachments(filing: Form700Filing, xml_tree: ET.Element) -> List[ScheduleA1]:
    attachments = []
    elements = xml_tree.findall('schedule_a_1s/schedule_a_1')
    for element in elements:
        attachment = ScheduleA1(
            id=UUID(element.findtext('id')),
            filing=filing,
            date_acquired=clean_datetime(element.findtext('date_acquired')),
            date_disposed=clean_datetime(element.findtext('date_disposed')),
            description=element.findtext('description'),
            name_of_business_entity=element.findtext('name_of_business_entity'),
            fair_market_value=clean_choice(
                element.findtext('fair_market_value'),
                ScheduleA1.fair_market_value_choices
            ),
            nature_of_investment=clean_choice(
                element.findtext('nature_of_investment'),
                ScheduleA1.nature_of_investment_choices
            ),
            nature_of_investment_other_description=element.findtext('nature_of_investment_other_description'),
            partnership_amount=clean_choice(
                element.findtext('partnership_amount'),
                ScheduleA1.partnership_amount_choices
            ),
        )
        attachments.append(attachment)

    return attachments


def _save_models(instances: List[BaseModel]) -> None:
    for instance in instances:
        instance.save(force_insert=True)


def parse_filing(filing_id: str, raw_data: str) -> Form700Filing:
    xml_tree = ET.fromstring(raw_data)
    filing = Form700Filing(id=filing_id)

    with db.atomic() as transaction:
        try:
            filing = _parse_cover(filing, xml_tree)
            offices = _parse_offices(filing, xml_tree)
            schedule_a1_attachments = _parse_schedule_a1_attachments(filing, xml_tree)
            # filing = _parse_schedule_a2_attachments(filing, xml_tree)
            # filing = _parse_schedule_b_attachments(filing, xml_tree)
            # filing = _parse_schedule_c1_attachments(filing, xml_tree)
            # filing = _parse_schedule_c2_attachments(filing, xml_tree)
            # filing = _parse_schedule_d_attachments(filing, xml_tree)
            # filing = _parse_schedule_e_attachments(filing, xml_tree)
            _save_models([filing])
            _save_models(offices)
            _save_models(schedule_a1_attachments)
            return filing
        except Exception:  # pylint: disable=broad-except
            transaction.rollback()
            logger.exception(f'Failed to parse filing {filing_id}!')
            raise
