"""
This file contains database model definitions. We use these models
to aid in working with a temporary database for data cleansing.
"""
import csv
import io
import logging
import os
from typing import Any, List, Tuple

from peewee import AutoField, BooleanField, CharField, DecimalField, ForeignKeyField, IntegerField, Model, UUIDField
from playhouse.dataset import DataSet
from playhouse.sqlite_ext import SqliteExtDatabase, TimestampField

DATABASE: str = '/tmp/reporting.db'

db = SqliteExtDatabase(
    DATABASE,
    pragmas=(
        ('foreign_keys', 1),  # Enforce foreign-key constraints
    )
)
logger = logging.getLogger(__name__)


def close_connection():
    if not db.is_closed():
        db.close()


def destroy_database():
    close_connection()

    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        logger.info(f'Deleted database: {DATABASE}')
    else:
        logger.info(f'Database {DATABASE} not deleted since it does not exist.')


class BaseModel(Model):
    class Meta:
        database = db

    def __eq__(self, other: Any) -> bool:
        # NOTE: We intentionally don't call the parent method because
        # we do NOT want to compare `AutoField` primary key values, which
        # we only use for `internal_id`.

        fields = self._meta.sorted_fields

        for field in fields:
            if field.name == 'internal_id':
                continue

            self_value = getattr(self, field.name)
            other_value = getattr(other, field.name)
            if self_value != other_value:
                logger.error(f'Field {field.name} value of {self_value} is unequal to {other_value}')
                return False

        return True


class Form700Filing(BaseModel):
    id = CharField(primary_key=True)
    report_year = IntegerField()
    filer_id = CharField()
    amends = ForeignKeyField('self', null=True, default=None, backref='amendments')
    date_signed = TimestampField(utc=True, default=None)
    first_name = CharField()
    middle_name = CharField(null=True, default=None)
    last_name = CharField()
    comments_schedule_a1 = CharField(null=True, default=None)
    comments_schedule_a2 = CharField(null=True, default=None)
    comments_schedule_b = CharField(null=True, default=None)
    comments_schedule_c = CharField(null=True, default=None)
    comments_schedule_d = CharField(null=True, default=None)
    comments_schedule_e = CharField(null=True, default=None)


class Office(BaseModel):
    id = UUIDField(primary_key=True)
    filing = ForeignKeyField(Form700Filing, backref='offices')
    agency = CharField()
    division_board_district = CharField(null=True)
    position = CharField()
    is_primary = BooleanField()
    election_date = TimestampField(null=True, utc=True, default=None)
    assuming_date = TimestampField(null=True, utc=True, default=None)
    leaving_date = TimestampField(null=True, utc=True, default=None)


class AbstractSchedule(BaseModel):
    """ Base class for schedules. """

    # NOTE: This field only exists to support foreign keys
    # between schedules and their nested data.
    internal_id = AutoField()
    id = UUIDField()
    filing = ForeignKeyField(Form700Filing)

    class Meta:
        indexes = (
            (('id', 'filing'), True),
        )


class ScheduleA1(AbstractSchedule):
    """ Investments (stocks, bonds, and other interests). Ownership less than 10%. """
    fair_market_value_choices = ('2000-10000', '10001-100000', '100001-1000000', '1000000+')
    nature_of_investment_choices = ('stock', 'partnership', 'other',)
    partnership_amount_choices = ('0-499', '500+')

    date_acquired = TimestampField(null=True, utc=True, default=None)
    date_disposed = TimestampField(null=True, utc=True, default=None)
    name_of_business_entity = CharField()
    description = CharField()
    fair_market_value = CharField(choices=fair_market_value_choices)
    nature_of_investment = CharField(choices=nature_of_investment_choices)
    nature_of_investment_other_description = CharField(null=True)
    partnership_amount = CharField(choices=partnership_amount_choices, null=True)


# TODO Parse income sources
# TODO Parse properties
class ScheduleA2(AbstractSchedule):
    """ Investments, income, and assets of business entities/trusts. Ownership 10% or greater. """
    fair_market_value_choices = ('0-1999', '2000-10000', '10001-100000', '100001-1000000', '1000000+')
    gross_income_received_choices = ('0-499', '500-1000', '1001-10000', '10001-100000', '100000+')
    nature_of_investment_choices = ('sole_proprietorship', 'partnership', 'other',)

    address_city = CharField()
    address_state = CharField()
    address_zip = CharField()
    business_position = CharField(null=True, default=None)
    date_acquired = TimestampField(null=True, utc=True, default=None)
    date_disposed = TimestampField(null=True, utc=True, default=None)
    description = CharField(null=True, default=None)
    entity_name = CharField()
    fair_market_value = CharField(choices=fair_market_value_choices, null=True, default=None)
    gross_income_received = CharField(choices=gross_income_received_choices)
    nature_of_investment = CharField(choices=nature_of_investment_choices, null=True, default=None)
    nature_of_investment_other_description = CharField(null=True, default=None)


# TODO Parse loan data
class ScheduleB(AbstractSchedule):
    """ Interests in real property, including rental income. """
    fair_market_value_choices = ('2000-10000', '10001-100000', '100001-1000000', '1000000+')
    gross_income_received_choices = ('0-499', '500-1000', '1001-10000', '10001-100000', '100000+')
    nature_of_interest_choices = ('ownership', 'easement', 'leasehold', 'other')

    city = CharField()
    date_acquired = TimestampField(null=True, utc=True, default=None)
    date_disposed = TimestampField(null=True, utc=True, default=None)
    fair_market_value = CharField(choices=fair_market_value_choices)
    gross_income_received = CharField(choices=gross_income_received_choices, null=True, default=None)
    nature_of_interest = CharField(choices=nature_of_interest_choices)
    parcel_or_address = CharField()


class ScheduleBIncomeSource(BaseModel):
    id = UUIDField()
    schedule = ForeignKeyField(ScheduleB, backref='income_sources')
    name = CharField()


# TODO Process income_sources
class ScheduleC1(AbstractSchedule):
    """ Income received. """
    gross_income_received_choices = ('none', '500-1000', '1001-10000', '10001-100000', '100000+')
    # NOTE: This order is NOT the same as that printed on the form!
    reason_for_income_choices = (
        'salary', 'spouse_income', 'loan_repayment', 'partnership', 'sale', 'other', 'commission', 'rental_income',
    )

    address_city = CharField()
    address_state = CharField()
    address_zip = CharField()
    business_activity = CharField(null=True, default=None)
    business_position = CharField(null=True, default=None)
    gross_income_received = CharField(choices=gross_income_received_choices)
    name_of_income_source = CharField()
    reason_for_income = CharField(choices=reason_for_income_choices, null=True, default=None)
    reason_for_income_other = CharField(null=True, default=None)


class ScheduleC1IncomeSource(BaseModel):
    id = UUIDField()
    schedule = ForeignKeyField(ScheduleC1, backref='income_sources')
    name = CharField()


class ScheduleC2(AbstractSchedule):
    """ Loans received. """
    highest_balance_choices = ('500-1000', '1001-10000', '10001-100000', '100000+')
    loan_security_choices = ('none', 'personal_residence', 'real_property', 'guarantor', 'other')

    address_city = CharField()
    address_state = CharField()
    address_zip = CharField()
    business_activity = CharField(null=True, default=None)
    has_interest_rate = BooleanField()
    highest_balance = CharField(choices=highest_balance_choices)
    interest_rate = DecimalField()
    interest_rate_raw = CharField()
    loan_security = CharField(choices=loan_security_choices)
    loan_security_real_property_address_city = CharField(null=True, default=None)
    loan_security_real_property_address_state = CharField(null=True, default=None)
    loan_security_real_property_address_zip = CharField(null=True, default=None)
    name_of_lender = CharField()
    term = IntegerField()
    term_type = CharField()


class ScheduleD(AbstractSchedule):
    """ Gifts. """
    address_city = CharField()
    address_state = CharField()
    address_zip = CharField()
    business_activity = CharField(null=True, default=None)
    name_of_source = CharField()


class ScheduleDGift(BaseModel):
    id = UUIDField()
    schedule = ForeignKeyField(ScheduleD, backref='gifts')
    amount = DecimalField(decimal_places=2)
    description = CharField()
    gift_date = IntegerField()


class ScheduleE(AbstractSchedule):
    """ Income from gifts, travel payments, advances, and reimbursements. """
    type_of_payment_choices = ('gift', 'income')

    address_city = CharField()
    address_state = CharField()
    address_zip = CharField()
    amount = DecimalField(decimal_places=2)
    business_activity = CharField(null=True, default=None)
    end_date = IntegerField()
    is_nonprofit = BooleanField()
    is_other = BooleanField()
    made_speech = BooleanField()
    name_of_source = CharField()
    start_date = IntegerField()
    travel_description = CharField(null=True, default=None)
    type_of_payment = CharField(choices=type_of_payment_choices)


def get_model_classes() -> List[Model]:
    classes = [cls for cls in BaseModel.__subclasses__()]
    classes += [cls for cls in AbstractSchedule.__subclasses__()]
    classes.remove(AbstractSchedule)
    return classes


def build_tables():
    close_connection()
    db.connect(reuse_if_open=True)
    db.create_tables(get_model_classes())


def _table_to_csv(dataset: DataSet, table_name: str) -> io.StringIO:
    buffer = io.StringIO()
    table = dataset[table_name]
    dataset.freeze(table.all(), format='csv', file_obj=buffer, quoting=csv.QUOTE_ALL)
    buffer.seek(0)
    return buffer


def export_data_to_csv() -> List[Tuple[Model, io.StringIO]]:
    db.close()
    dataset = DataSet(f'sqlite:///{DATABASE}')
    models = get_model_classes()
    # pylint: disable=protected-access
    return [(model, _table_to_csv(dataset, model._meta.table_name)) for model in models]
