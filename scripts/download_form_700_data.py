#!/usr/bin/python
import datetime
import os

from pipeline.bigquery import is_connected, refresh_model_data
from pipeline.netfile.client import download_filing, get_filing_ids
from pipeline.netfile.models import build_tables, destroy_database, export_data_to_csv
from pipeline.netfile.parsers import parse_filing

FORM_TYPE = 254  # FPPC Form 700 Statement of Economic Interests (2018-2019)


def _save_file(directory: str, filing_id: str, content: str) -> None:
    file_path = os.path.join(directory, f'{filing_id}.xml')
    with open(file_path, 'w') as output:
        output.write(content)


def main():
    # Ensure we can connect to the data warehouse
    is_connected()

    # Setup the intermediary database
    destroy_database()
    build_tables()

    # Create the download directory
    directory = os.path.join(os.path.dirname(__file__), datetime.datetime.now().isoformat())
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Get a list of filing IDs
    filing_ids = get_filing_ids(FORM_TYPE)

    # Download the filings
    for filing_id in filing_ids:
        content = download_filing(filing_id)
        _save_file(directory, filing_id, content)
        parse_filing(filing_id, content)

    # Export the data to the data warehouse
    for model, data in export_data_to_csv():
        refresh_model_data(model, data)


if __name__ == '__main__':
    main()
