import asyncio
import logging
import os
from contextlib import closing, contextmanager
from datetime import datetime
from fileinput import FileInput
from pathlib import Path
from zoneinfo import ZoneInfo

import boto3
from botocore.client import Config

from folioclient import FolioClient
from folio_data_import.UserImport import UserImporter

PWD = Path.cwd()
USERS_FILE = PWD / "users.ndjson"
ERRORS_FILE = PWD / f"errors"
LOG_FILE = PWD / f"log"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())

async def import_users():
    library_name = os.getenv("LIBRARY_NAME")
    library_code = os.getenv("LIBRARY_CODE")
    logger.info(f"Replacing {library_name} with {library_code}")
    with FileInput(USERS_FILE, inplace=True) as file:
        for line in file:
            print(line.replace(library_name, library_code), end='')

    logger.info("Setting up Importer")
    importer = UserImporter(
        FolioClient(
            os.getenv("FOLIO_URL"),
            os.getenv("FOLIO_TENANT"),
            os.getenv("FOLIO_USERNAME"),
            os.getenv("FOLIO_PASSWORD"),
        ),
        library_name=os.getenv("LIBRARY_NAME"),
        batch_size=os.getenv("BATCH_SIZE"),
        only_update_present_fields=os.getenv("ONLY_UPDATE_PRESENT_FIELDS", 1) == 1,
        user_file_path=USERS_FILE,
        limit_simultaneous_requests=asyncio.Semaphore(10),
        no_progress=True,
    )
    await importer.setup(ERRORS_FILE)
    logger.info("Importing")
    await importer.do_import()


@contextmanager
def _create_spaces_client(key, secret):
    session = boto3.session.Session()
    with closing(session.client(
        's3',
        region_name=os.getenv('SPACES_REGION', 'nyc3'),
        endpoint_url=os.getenv('SPACES_ENDPOINT', 'https://nyc3.digitaloceanspaces.com'),
        aws_access_key_id=key,
        aws_secret_access_key=secret,
        config=Config(s3={'addressing_style': 'virtual'})
        )) as s3:
        yield s3


def download_users():
    bucket = os.getenv('USERS_BUCKET')

    logger.info(f"Finding latest users file in: {bucket}")
    users_key = None
    with _create_spaces_client(os.getenv('USERS_KEY'), os.getenv('USERS_SECRET')) as s3:
        paginator = s3.get_paginator("list_objects_v2")
        latest = None
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get("Contents", []):
                if obj["Key"].startswith("failed_users"):
                    continue
                if (latest is None) or (obj["LastModified"] > latest["LastModified"]):
                    latest = obj
        users_key = latest["Key"] if latest else None

    logger.info(f"downloading latest users file: {users_key}")
    with open(USERS_FILE, "wb+") as users_file:
        s3.download_fileobj(bucket, users_key, users_file)

def upload_logs():
    users_bucket = os.getenv('USERS_BUCKET')
    logs_bucket = os.getenv('LOGS_BUCKET')

    now = datetime.now(ZoneInfo(os.getenv('TIMEZONE', "America/New_York"))).isoformat()

    with _create_spaces_client(os.getenv('USERS_KEY'), os.getenv('USERS_SECRET')) as s3:
        if ERRORS_FILE.exists() and ERRORS_FILE.stat().st_size > 0:
            logger.info(f"Uploading errord users file to: {users_bucket}")
            s3.upload_file(ERRORS_FILE, users_bucket, f"failed_users_{now}.ndjson")
        else:
            logger.info(f"No errors file")

    with _create_spaces_client(os.getenv('LOGS_KEY'), os.getenv('LOGS_SECRET')) as s3:
        library = " ".join(os.getenv("LIBRARY_NAME").strip('"').split()[:-1])
        logger.info(f"Uploading logs file to: {logs_bucket}/{library}_{now}.log")
        s3.upload_file(LOG_FILE, logs_bucket, f"{library}_{now}.log")

async def notify_error(ex):
    # TODO: post ex to slack
    ...

async def main():
    try:
        download_users()
        await import_users()
        upload_logs()
    except Exception as ex:
        await notify_error(ex)
        raise

if __name__ == "__main__":
    asyncio.run(main())
