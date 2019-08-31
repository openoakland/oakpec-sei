import io
import logging
from typing import List, Union

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from peewee import Field, Model

from .netfile.models import (
    Form700Filing, Office, ScheduleA1, ScheduleA2, ScheduleB, ScheduleBIncomeSource, ScheduleC1, ScheduleC2, ScheduleD,
    ScheduleDGift, ScheduleE
)

logger = logging.getLogger(__name__)

PROJECT_ID: str = 'openoakland'
DATASET_ID: str = 'ethics'


def is_connected() -> bool:
    client = bigquery.Client()

    try:
        client.get_service_account_email()
    except Exception:  # pylint: disable=broad-except
        return False

    return True


def _stringio2bytesio(data: io.StringIO) -> io.BytesIO:
    return io.BytesIO(data.getvalue().encode('utf8'))


def _recreate_table(client: bigquery.Client, table_id: str, schema: list) -> None:
    logger.info(f'Recreating {table_id} table...')
    dataset_ref = client.dataset(DATASET_ID)
    table_ref = dataset_ref.table(table_id)
    table = bigquery.Table(table_ref, schema=schema)
    client.delete_table(table_ref, not_found_ok=True)
    client.create_table(table)


def _refresh_table_data(table_id: str, schema: List[bigquery.SchemaField], source_file: Union[io.BytesIO, io.IOBase]):
    client = bigquery.Client()
    _recreate_table(client, table_id, schema)

    logger.info(f'Loading {table_id} data into BigQuery...')
    dataset_ref = client.dataset(DATASET_ID)
    table_ref = dataset_ref.table(table_id)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1
    )

    job = client.load_table_from_file(
        source_file,
        table_ref,
        location='US',
        job_config=job_config
    )

    try:
        # Wait for the loading to complete
        job.result()
        logger.info(f'Loaded {job.output_rows} rows into {DATASET_ID}:{table_id}.')
    except GoogleCloudError as e:
        logger.exception(f'Failed to push data to {DATASET_ID}:{table_id}: {e.errors}')


def _get_type_for_field(field: Field) -> str:
    field_type = field.field_type
    return {
        'auto': 'INT64',
        'bigint': 'INT64',
        'bool': 'BOOL',
        'decimal': 'NUMERIC',
        'int': 'INT64',
        'uuid': 'STRING',
        'varchar': 'STRING',
    }[field_type.lower()]


def _get_schema_for_field(field: Field) -> bigquery.SchemaField:
    mode = 'NULLABLE' if field.null else 'REQUIRED'
    field_type = _get_type_for_field(field)
    return bigquery.SchemaField(field.name, field_type, mode=mode)


def _get_schema_for_model(model: Model) -> List[bigquery.SchemaField]:
    return [_get_schema_for_field(field) for field in model._meta.sorted_fields]  # pylint: disable=protected-access


def _get_table_id_for_model(model: Model) -> str:
    return {
        Form700Filing: 'filings',
        Office: 'offices',
        ScheduleA1: 'schedule_a1_attachments',
        ScheduleA2: 'schedule_a2_attachments',
        ScheduleB: 'schedule_b_attachments',
        ScheduleBIncomeSource: 'schedule_b_income_sources',
        ScheduleC1: 'schedule_c1_attachments',
        ScheduleC2: 'schedule_c2_attachments',
        ScheduleD: 'schedule_d_attachments',
        ScheduleDGift: 'schedule_d_gifts',
        ScheduleE: 'schedule_e_attachments',
    }[model]


def refresh_model_data(model: Model, data: io.StringIO) -> None:
    data.seek(0)
    source_file = _stringio2bytesio(data)
    schema = _get_schema_for_model(model)
    table_id = _get_table_id_for_model(model)
    _refresh_table_data(table_id, schema, source_file)
