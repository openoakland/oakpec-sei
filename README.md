# Public Ethics Data Downloader [![CircleCI](https://circleci.com/gh/openoakland/oakpec-sei/tree/master.svg?style=svg)](https://circleci.com/gh/openoakland/oakpec-sei/tree/master) [![codecov](https://codecov.io/gh/openoakland/oakpec-sei/branch/master/graph/badge.svg)](https://codecov.io/gh/openoakland/oakpec-sei)

This repository contains scripts used to download ethics data for the [City of Oakland](https://www.oaklandca.gov/boards-commissions/public-ethics-commission).

We currently support retrieving the 2018-2019 [FPPC Form 700 Statement of Economic Interests](http://www2.oaklandnet.com/government/o/CityAdministration/d/PublicEthics/s/government-ethics/form-700/index.htm).
The data is downloaded from [Netfile](https://netfile.com/Connect2/api/swagger-ui/#!/public/) and uploaded to a data
warehouse.

## Usage
The logic to download and parse filings is normally deployed to Google Cloud as cloud functions.

The logic can also be run locally as scripts in the `scripts` directory. `download_form_700_data.py` will download all
filings to `scripts/filings`. `parse_local_data.py` will extract data from the downloaded files to a SQLite database.

These scripts can be run with a command like the one below:

    python -m scripts.download_form_700_data

## Development
We use [`pipenv`](https://docs.pipenv.org/en/latest/) to manage environments and requirements, so install that first.

1. Install the requirements for this project:

    ```
    make requirements
    ```

2. Run code quality inspection:

    ```
    make quality
    ```

3. Run tests:

    ```
    make test
    ```

## Deployment
This code is deployed to Google Cloud as functions responsible for (a) downloading filings and (b) performing ETL.
The functions can all be deployed by running `./deploy.sh`.
