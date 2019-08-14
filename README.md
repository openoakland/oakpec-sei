# Public Ethics Data Downloader [![CircleCI](https://circleci.com/gh/openoakland/oakpec-sei/tree/master.svg?style=svg)](https://circleci.com/gh/openoakland/oakpec-sei/tree/master) [![codecov](https://codecov.io/gh/openoakland/oakpec-sei/branch/master/graph/badge.svg)](https://codecov.io/gh/openoakland/oakpec-sei)

This repository contains scripts used to download ethics data for the [City of Oakland](https://www.oaklandca.gov/boards-commissions/public-ethics-commission).

We currently support retrieving the 2018-2019 [FPPC Form 700 Statement of Economic Interests](http://www2.oaklandnet.com/government/o/CityAdministration/d/PublicEthics/s/government-ethics/form-700/index.htm).
The data is downloaded from [Netfile](https://netfile.com/Connect2/api/swagger-ui/#!/public/) and uploaded to a data 
warehouse.

## Development
We use [`pipenv`](https://docs.pipenv.org/en/latest/) to manage environments and requirements, so install that first.

1. Install the requirements for this project:
    ```bash
    make requirements
    ```

2. Run code quality inspection:
    ```bash
    make quality
    ```

3. Run tests:
    ```bash
    make test
    ```
