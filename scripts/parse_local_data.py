#!/usr/bin/python
import os
import re
from pathlib import Path

from pipeline.netfile.models import build_tables, destroy_database
from pipeline.netfile.parsers import parse_filing

FORM_TYPE = 254  # FPPC Form 700 Statement of Economic Interests (2018-2019)

DIRECTORY_NAME = 'filings'


def _save_file(directory: str, filing_id: str, content: str) -> None:
    file_path = os.path.join(directory, f'{filing_id}.xml')
    with open(file_path, 'w') as output:
        output.write(content)


def main():
    # Setup the intermediary database
    destroy_database()
    build_tables()

    # Iterate over filings
    directory = os.path.join(os.path.dirname(__file__), DIRECTORY_NAME)
    paths = Path(directory).glob('**/*.xml')
    for path in paths:
        match = re.search(r'(\d+)\.xml', str(path))
        filing_id = match[1]

        with open(str(path)) as f:
            content = f.read()

        parse_filing(filing_id, content)


if __name__ == '__main__':
    main()
