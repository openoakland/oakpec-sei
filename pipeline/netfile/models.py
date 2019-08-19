"""
This file contains database model definitions. We use these models
to aid in working with a temporary database for data cleansing.
"""
import csv
import io
import logging
import os
from typing import Any, List, Tuple

from peewee import BooleanField, CharField, ForeignKeyField, IntegerField, Model, UUIDField
from playhouse.dataset import DataSet
from playhouse.sqlite_ext import SqliteExtDatabase, TimestampField

DATABASE: str = '/tmp/reporting.db'

db = SqliteExtDatabase(DATABASE, pragmas=(
    # ('cache_size', -1024 * 64),  # 64MB page-cache.
    # ('journal_mode', 'wal'),  # Use WAL-mode (you should always use this!).
    ('foreign_keys', 1),))  # Enforce foreign-key constraints.
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

    # TODO Remove once https://github.com/coleifer/peewee/issues/1993 is resolved
    def __eq__(self, other: Any) -> bool:
        if not super().__eq__(other):
            return False

        for field in self._meta.sorted_fields:
            if getattr(self, field.name) != getattr(other, field.name):
                return False

        return True


class Form700Filing(BaseModel):
    id = CharField(primary_key=True)
    report_year = IntegerField()
    filer_id = CharField()
    date_signed = TimestampField(utc=True, default=None)
    first_name = CharField()
    middle_name = CharField(null=True)
    last_name = CharField()


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


class ScheduleA1(BaseModel):
    fair_market_value_choices = ('2000-10000', '10001-100000', '100001-1000000', '1000000+')
    nature_of_investment_choices = ('stock', 'partnership', 'other',)
    partnership_amount_choices = ('0-499', '500+')

    id = UUIDField(primary_key=True)
    filing = ForeignKeyField(Form700Filing, backref='schedule_a1_attachments')
    date_acquired = TimestampField(null=True, utc=True, default=None)
    date_disposed = TimestampField(null=True, utc=True, default=None)
    name_of_business_entity = CharField()
    description = CharField()
    fair_market_value = CharField(choices=fair_market_value_choices)
    nature_of_investment = CharField(choices=nature_of_investment_choices)
    nature_of_investment_other_description = CharField(null=True)
    partnership_amount = CharField(choices=partnership_amount_choices, null=True)

    """
    <date_acquired />
      <date_disposed />
      <description>Equipment and Technologies</description>
      <fair_market_value>1</fair_market_value>
      <name_of_business_entity>Applied Materials</name_of_business_entity>
      <nature_of_investment>1</nature_of_investment>
      <partnership_amount>0</partnership_amount>
      <id>2fcdab47-276c-477a-82cc-5dcbeb1e8bf8</id>
      <version_for_add>0</version_for_add>
      <version_for_delete>0</version_for_delete>
      <version_for_edit>0</version_for_edit>
      """


def build_tables():
    close_connection()
    db.connect(reuse_if_open=True)
    db.create_tables([cls for cls in BaseModel.__subclasses__()])


def _table_to_csv(dataset: DataSet, table_name: str) -> io.StringIO:
    buffer = io.StringIO()
    table = dataset[table_name]
    dataset.freeze(table.all(), format='csv', file_obj=buffer, quoting=csv.QUOTE_ALL)
    buffer.seek(0)
    return buffer


def export_data_to_csv() -> List[Tuple[Model, io.StringIO]]:
    db.close()
    dataset = DataSet(f'sqlite:///{DATABASE}')
    models: List[Model] = [cls for cls in BaseModel.__subclasses__()]
    # pylint: disable=protected-access
    return [(model, _table_to_csv(dataset, model._meta.table_name)) for model in models]
