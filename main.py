import datetime
import logging
import re

from google.cloud import pubsub_v1, storage

from pipeline.bigquery import is_connected, refresh_model_data
from pipeline.netfile.client import download_filing, get_filing_ids
from pipeline.netfile.models import build_tables, destroy_database, export_data_to_csv
from pipeline.netfile.parsers import parse_filing

PROJECT_ID = 'openoakland'
BUCKET_NAME = 'form-700-filings'

logger = logging.getLogger(__name__)


def download_netfile_filing(data: dict, context) -> None:
    """ Download an individual Netfile filing. """
    attributes = data['attributes']
    filing_id = attributes['filing_id']
    parent_directory = attributes['parent_directory']
    filename = f'{filing_id}.xml'

    content = download_filing(filing_id)

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(f'{parent_directory}/{filename}')
    blob.upload_from_string(content, content_type='text/xml')


def download_all_filings(data: dict, context) -> None:
    """ Trigger a download of all Netfile filings of a given type. """
    parent_directory = datetime.datetime.now().isoformat()
    topic_name = 'download-netfile-filing'
    attributes = data['attributes']
    form_type = attributes['form_type']

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, topic_name)

    filing_ids = get_filing_ids(form_type)

    for filing_id in filing_ids:
        publisher.publish(topic_path, data=''.encode('utf-8'), filing_id=filing_id, parent_directory=parent_directory)


def process_netfile_filings(data: dict, context) -> None:
    """ Process all filings in a given directory. """
    attributes = data['attributes']
    directory = attributes['directory']

    # Ensure we can connect to the data warehouse
    is_connected()

    # Setup the intermediary database
    destroy_database()
    build_tables()

    # Read the files
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(BUCKET_NAME, prefix=f'{directory}/')
    for blob in blobs:
        match = re.search(rf'{directory}/(\d+)\.xml', blob.name)
        if not match:
            logger.warning(f'File name "{blob.name}" does not match the expected format')
            continue

        filing_id = match.group(1)
        content = blob.download_as_string().decode('utf8')
        parse_filing(filing_id, content)

    # Export the data to the data warehouse
    for model, export in export_data_to_csv():
        try:
            bucket = storage_client.get_bucket(BUCKET_NAME)
            blob = bucket.blob(f'{directory}/{model.__name__}.csv')
            blob.upload_from_file(export, rewind=True, content_type='text/csv')
            refresh_model_data(model, export)
        except Exception:
            logger.exception(f'Failed to upload data for #{model} to BigQuery')
