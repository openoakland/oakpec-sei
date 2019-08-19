#! /bin/sh

set -x

PIPENV_DONT_USE_PYENV=1 PIPENV_SYSTEM=1 pipenv lock --python=`which python` -r > requirements.txt

gcloud config set project openoakland

gcloud components install beta --quiet

# Deploy function get all filings
gcloud functions deploy \
    download-all-filings \
    --runtime=python37 \
    --memory=256MB \
    --entry-point=download_all_filings \
    --trigger-topic=download-all-filings \
    --timeout=120

# Deploy function to download files
gcloud functions deploy \
    download-netfile-filing \
    --runtime=python37 \
    --memory=256MB \
    --entry-point=download_netfile_filing \
    --trigger-topic=download-netfile-filing \
    --timeout=120

# Deploy function to transform and load the files
gcloud functions deploy \
    process-netfile-filings \
    --runtime=python37 \
    --memory=256MB \
    --entry-point=process_netfile_filings \
    --trigger-topic=process-netfile-filings \
    --timeout=300
