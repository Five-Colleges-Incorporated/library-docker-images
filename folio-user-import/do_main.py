"""Entrypoint for nightly user import."""

import asyncio
import logging
import os
from contextlib import closing, contextmanager
from datetime import datetime
from fileinput import FileInput
from pathlib import Path
from zoneinfo import ZoneInfo

import boto3
from folio_data_import.UserImport import UserImporter
from folioclient import FolioClient

PWD = Path.cwd()
USERS_FILE = PWD / "users.ndjson"
ERRORS_FILE = PWD / "errors"
LOG_FILE = PWD / "log"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())


class NoUserFileError(Exception):
    """Raised when a user file cannot be found with the configured prefix."""

    def __init__(self):
        """Initialize a new NoUserFileError."""
        msg = f"No file found for prefix '{os.getenv('USERS_PREFIX')}*'"
        super().__init__(msg)


async def import_users():
    """Imports users via the folio_data_import library."""
    library_name = os.getenv("LIBRARY_NAME")
    library_code = os.getenv("LIBRARY_CODE")
    logger.info("Replacing %s with %s", library_name, library_code)
    with FileInput(USERS_FILE, inplace=True) as file:
        for line in file:
            # new lines at the end of the file choke the import
            # I'm not 100% sure if FileInput has the \n character in the string
            # but anything shorter than 5 can't possibly be a valid user anyways
            if len(line) >= 5:
                print(line.replace(library_name, library_code), end="")  # noqa: T201

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
        only_update_present_fields=os.getenv("ONLY_UPDATE_PRESENT_FIELDS", "1") == "1",
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
    with closing(
        session.client(
            "s3",
            region_name=os.getenv("SPACES_REGION", "nyc3"),
            endpoint_url=os.getenv(
                "SPACES_ENDPOINT",
                "https://nyc3.digitaloceanspaces.com",
            ),
            aws_access_key_id=key,
            aws_secret_access_key=secret,
        ),
    ) as s3:
        yield s3


def download_users():
    """Dowloads the latest uploaded users file to a fixed location."""
    bucket = os.getenv("USERS_BUCKET")

    logger.info("Finding latest users file in: %s", bucket)
    users_key = None
    with _create_spaces_client(os.getenv("USERS_KEY"), os.getenv("USERS_SECRET")) as s3:
        paginator = s3.get_paginator("list_objects_v2")
        latest = None
        for page in paginator.paginate(
            Bucket=bucket,
            Prefix=os.getenv("USERS_PREFIX", ""),
        ):
            for obj in page.get("Contents", []):
                if (latest is None) or (obj["LastModified"] > latest["LastModified"]):
                    latest = obj
        users_key = latest["Key"] if latest else None

    if users_key is None:
        raise NoUserFileError

    logger.info("downloading latest users file: %s", users_key)
    with USERS_FILE.open("wb+") as users_file:
        s3.download_fileobj(bucket, users_key, users_file)


def upload_logs():
    """Uploads the errors and logs after the import."""
    users_bucket = os.getenv("USERS_BUCKET")
    logs_bucket = os.getenv("LOGS_BUCKET")

    now = datetime.now(ZoneInfo(os.getenv("TIMEZONE", "America/New_York"))).isoformat()

    with _create_spaces_client(os.getenv("USERS_KEY"), os.getenv("USERS_SECRET")) as s3:
        if ERRORS_FILE.exists() and ERRORS_FILE.stat().st_size > 0:
            logger.info("Uploading errored users file to: %s", users_bucket)
            s3.upload_file(ERRORS_FILE, users_bucket, f"failed_users_{now}.ndjson")
        else:
            logger.info("No errors file")

    with _create_spaces_client(os.getenv("LOGS_KEY"), os.getenv("LOGS_SECRET")) as s3:
        library = " ".join(os.getenv("LIBRARY_NAME", "").strip('"').split()[:-1])
        log_key = f"{library}_{now}.log"
        logger.info("Uploading log file to: %s/%s", logs_bucket, log_key)
        s3.upload_file(LOG_FILE, logs_bucket, log_key)


async def main():
    """The cli entrypoint to run the full import."""
    download_users()
    try:
        await import_users()
    finally:
        upload_logs()


if __name__ == "__main__":
    asyncio.run(main())
