"""
This file contains client code for the Netfile API.
"""
import io
import logging
import zipfile
from typing import Set

import requests

from .errors import DownloadError

AID = 'coak'
API_ROOT = 'https://netfile.com/Connect2/api'
DEFAULT_HEADERS = {
    'Accept': 'application/json',
}

logger = logging.getLogger(__name__)


def build_url(path: str) -> str:
    return f'{API_ROOT}/{path}'


def get_filing_ids(form_type: int) -> Set[str]:
    """
    Returns a list of filing IDs corresponding to the given form type.
    """
    url = build_url('public/list/filing')
    page = 0

    filings = set()
    ignored_filings = set()

    while True:
        logger.info(f'Retrieving page {page} of form type {form_type} data...')
        data = {
            'AID': AID,
            'Form': form_type,
            'CurrentPageIndex': page,
        }
        response = requests.post(url, data=data, headers=DEFAULT_HEADERS)

        if response.status_code != 200:
            msg = f'Failed to download page {page} of the form type {form_type} data!'
            try:
                content = response.json()
            except Exception:  # pylint: disable=broad-except
                content = response.content

            logger.error(f'{msg}\nstatus_code: {response.status_code}\ncontent: {content}')
            raise DownloadError(msg)

        response_data = response.json().get('filings')

        # If we don't have any more filings, we've reached the end of the data set.
        if not response_data:
            break

        for datum in response_data:
            filing_id = str(datum['id'])
            if datum.get('isEfiled', False):
                filings.add(filing_id)
            else:
                ignored_filings.add(filing_id)
                logger.info(f'Ignoring filing {filing_id}. This filing was not filed electronically.')

        page += 1

    msg = f'Finished retrieving {len(filings)} filing IDs. {len(ignored_filings)} filings were ignored because they ' \
          f'were not filed electronically.'
    logger.info(msg)

    return filings


def download_filing(filing_id: str) -> str:
    """ Downloads the XML for the given filing. """
    logger.info(f'Downloading filing {filing_id}...')
    url = build_url(f'public/efile/{filing_id}')
    response = requests.get(url, headers=DEFAULT_HEADERS, stream=True)

    if response.status_code != 200:
        msg = f'Failed to download filing {filing_id}!'
        try:
            content = response.json()
        except Exception:  # pylint: disable=broad-except
            content = response.content
        logger.error(f'{msg}\nstatus_code: {response.status_code}\ncontent: {content}')
        raise DownloadError(msg)

    downloaded_file = zipfile.ZipFile(io.BytesIO(response.content))
    text = downloaded_file.read('Efile.txt').decode('utf8')

    logger.info(f'Successfully downloaded filing {filing_id}.')
    return text.strip()
