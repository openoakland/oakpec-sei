import os

import pytest
import responses

from ..client import build_url, download_filing, get_filing_ids
from ..errors import DownloadError

FORM_TYPE = 254


def test_build_url():
    assert build_url('test') == 'https://netfile.com/Connect2/api/test'
    assert build_url('public/list/filing') == 'https://netfile.com/Connect2/api/public/list/filing'


@responses.activate
def test_get_filings():
    page_0 = {
        'filings': [
            {
                'id': 1,
            },
            {
                'id': 2,
                'isEfiled': True,
            },
        ]
    }
    page_1 = {
        'filings': [
            {
                'id': 3,
                'isEfiled': True,
            },
            {
                'id': 4,
                'isEfiled': True,
            },
        ]
    }
    url = build_url('public/list/filing')
    responses.add(responses.POST, url, json=page_0)
    responses.add(responses.POST, url, json=page_1)
    responses.add(responses.POST, url, json={})

    actual = get_filing_ids(FORM_TYPE)
    assert actual == {'2', '3', '4'}


@responses.activate
def test_get_filings_error():
    responses.add(responses.POST, build_url('public/list/filing'), status=500)

    with pytest.raises(DownloadError):
        get_filing_ids(FORM_TYPE)


@responses.activate
def test_download_filing():
    filing_id = '1234'
    file_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'dummy_filing.zip')
    with open(file_path, 'rb') as test_file:
        responses.add(responses.GET, build_url(f'public/efile/{filing_id}'), body=test_file.read(), stream=True)
    assert download_filing(filing_id) == 'This is a test file!'


@responses.activate
def test_download_filing_error():
    filing_id = '1234'
    responses.add(responses.GET, build_url(f'public/efile/{filing_id}'), status=500)

    with pytest.raises(DownloadError):
        download_filing(filing_id)
