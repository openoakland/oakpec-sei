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
XML_DIRECTORY_NAME = 'xml'
FILING_MANIFEST_FILENAME = 'filings.txt'

logger = logging.getLogger(__name__)


def download_all_filings(data: dict, context) -> None:  # pylint: disable=unused-argument
    """ Trigger a download of all Netfile filings of a given type. """
    parent_directory = datetime.datetime.now().isoformat()
    topic_name = 'download-netfile-filing'
    attributes = data['attributes']
    form_type = attributes['form_type']

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, topic_name)  # pylint: disable=no-member

    filing_ids = get_filing_ids(form_type)

    # Store a list of the filing IDs
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(f'{parent_directory}/{FILING_MANIFEST_FILENAME}')
    blob.upload_from_string('\n'.join(filing_ids), content_type='text/plain')

    for filing_id in filing_ids:
        publisher.publish(topic_path, data=''.encode('utf-8'), filing_id=filing_id, parent_directory=parent_directory)


def trigger_processing(storage_client: storage.Client, parent_directory: str):
    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(f'{parent_directory}/{FILING_MANIFEST_FILENAME}')
    manifest_file = blob.download_as_string().decode('utf8')
    expected_count = len(manifest_file.split('\n'))

    actual_count = 0
    blobs = storage_client.list_blobs(BUCKET_NAME, prefix=f'{parent_directory}/{XML_DIRECTORY_NAME}/')
    for _ in blobs:
        actual_count += 1

    if actual_count == expected_count:
        logger.info('All %d files downloaded. Starting processing.', actual_count)
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, 'process-netfile-filings')  # pylint: disable=no-member
        publisher.publish(topic_path, b'', directory=parent_directory)
    else:
        logger.debug('Only %d of %d filings downloaded. Waiting to start processing.', actual_count, expected_count)


def download_netfile_filing(data: dict, context) -> None:  # pylint: disable=unused-argument
    """ Download an individual Netfile filing. """
    attributes = data['attributes']
    filing_id = attributes['filing_id']
    parent_directory = attributes['parent_directory']
    filename = f'{filing_id}.xml'

    content = download_filing(filing_id)

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(f'{parent_directory}/{XML_DIRECTORY_NAME}/{filename}')
    blob.upload_from_string(content, content_type='text/xml')

    trigger_processing(storage_client, parent_directory)


def process_netfile_filings(data: dict, context) -> None:  # pylint: disable=unused-argument
    """ Process all filings in a given directory. """
    attributes = data['attributes']
    directory = attributes['directory']
    xml_directory = f'{directory}/{XML_DIRECTORY_NAME}'

    # Ensure we can connect to the data warehouse
    is_connected()

    # Setup the intermediary database
    destroy_database()
    build_tables()

    # Read the files
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(BUCKET_NAME, prefix=f'{xml_directory}/')
    for blob in blobs:
        match = re.search(rf'{xml_directory}/(\d+)\.xml', blob.name)
        if not match:
            logger.warning(f'File name "{blob.name}" does not match the expected format')
            continue

        filing_id = match.group(1)
        content = blob.download_as_string().decode('utf8')
        parse_filing(filing_id, content)

    # Export the data to the data warehouse
    for model, export in export_data_to_csv():
        try:
            # Backup the CSVs in case we need them later
            bucket = storage_client.get_bucket(BUCKET_NAME)
            blob = bucket.blob(f'{directory}/csv/{model.__name__}.csv')
            blob.upload_from_file(export, rewind=True, content_type='text/csv')

            refresh_model_data(model, export)
        except Exception:  # pylint: disable=broad-except
            logger.exception(f'Failed to upload data for #{model} to BigQuery')
