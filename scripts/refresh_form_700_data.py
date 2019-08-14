#!/usr/bin/python
import csv
import io
import os
from typing import List, Tuple

from peewee import Model
from playhouse.dataset import DataSet

from pipeline.bigquery import is_connected, refresh_model_data
from pipeline.netfile.models import DATABASE, BaseModel, Form700Filing, build_tables, destroy_database
from pipeline.netfile.parsers import parse_filing


def _table_to_csv(dataset: DataSet, table_name: str) -> io.StringIO:
    buffer = io.StringIO()
    table = dataset[table_name]
    dataset.freeze(table.all(), format='csv', file_obj=buffer, quoting=csv.QUOTE_ALL)
    buffer.seek(0)
    return buffer


def _get_cleaned_data() -> List[Tuple[Model, io.StringIO]]:
    dataset = DataSet(f'sqlite:///{DATABASE}')
    models: List[Model] = [cls for cls in BaseModel.__subclasses__()]
    return [(model, _table_to_csv(dataset, model._meta.table_name)) for model in models]


def main():
    # Ensure we can connect to the data warehouse
    is_connected()

    # Setup the intermediary database
    destroy_database()
    build_tables()

    # TODO Download all filings
    # TODO Store filings locally so we can re-parse them without downloading, if needed.
    filing_id = '182305528'
    file_path = os.path.join(os.path.dirname(__file__), f'{filing_id}.xml')
    with open(file_path, 'r') as test_file:
        raw_xml = test_file.read()
    parse_filing(filing_id, raw_xml)

    # Export the data to the data warehouse
    for model, data in _get_cleaned_data():
        refresh_model_data(model, data)


if __name__ == '__main__':
    main()
