"""Entrypoint for nightly user import."""

import logging
import os
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import boto3
import dotenv
from transformPatronData import PatronDataTransformer

PWD = Path.cwd()
USERS_FILE = PWD / "users.ndjson"
OUTPUT_DIR = PWD / "output"
LOG_FILE = PWD / "log"
STAFF_CONDENSED_PREFIX = "condensed/staff_"
STUDENT_CONDENSED_PREFIX = "condensed/student_"


logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())


class NoRequiredFileError(Exception):
    """Raised when a file cannot be found with the configured prefix."""

    def __init__(self, prefix):
        """Initialize a new NoUserFileError."""
        msg = f"No file found for prefix '{prefix}*'"
        super().__init__(msg)


def transform_users():
    """Transforms users via the UMass Patron Transform script."""
    config = ".env"
    dotenv.load_dotenv(config)
    converter = PatronDataTransformer(config, datetime.now(UTC))
    converter.preparePatronLoad()


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


def _dowload_latest(prefix, name, required=False):
    bucket = os.getenv("USERS_BUCKET")

    logger.info("Finding latest %s file in: %s", prefix, bucket)
    key = None
    with _create_spaces_client(
        os.getenv("ACCESS_KEY"),
        os.getenv("ACCESS_SECRET"),
    ) as s3:
        paginator = s3.get_paginator("list_objects_v2")
        latest = None
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                if (latest is None) or (obj["LastModified"] > latest["LastModified"]):
                    latest = obj
        key = latest["Key"] if latest else None

    if key is None and not required:
        return None

    if key is None:
        raise NoRequiredFileError(prefix)

    logger.info("downloading latest file %s to %s", key, name)
    with Path(name).open("wb+") as named_file:
        s3.download_fileobj(bucket, key, named_file)

    return key


def download_users():
    """Downloads input files and previously condensed files."""
    full_load = os.getenv("FORCE_FULL_LOAD", "0") == "1" or (
        _dowload_latest(STAFF_CONDENSED_PREFIX, "staff_condense") is not None
        and _dowload_latest(STUDENT_CONDENSED_PREFIX, "student_condense") is not None
    )
    os.environ["fullLoad"] = str(full_load)  # noqa: SIM112

    _dowload_latest(os.getenv("STAFF_PREFIX"), "staff_input", required=True)
    _dowload_latest(os.getenv("STUDENT_PREFIX"), "student_input", required=True)


def upload_users(now: str):
    """Uploads the errors and logs after the import."""
    users_bucket = os.getenv("BUCKET")

    with _create_spaces_client(
        os.getenv("ACCESS_KEY"),
        os.getenv("ACCESS_SECRET"),
    ) as s3:
        logger.info("Uploading condensed staff file to: %s", users_bucket)
        s3.upload_file(
            OUTPUT_DIR / "Staff-Condensed.csv",
            users_bucket,
            f"{STAFF_CONDENSED_PREFIX}{now}.csv",
        )

        logger.info("Uploading condensed student file to: %s", users_bucket)
        s3.upload_file(
            OUTPUT_DIR / "Student-Condensed.csv",
            users_bucket,
            f"{STUDENT_CONDENSED_PREFIX}{now}.csv",
        )

        logger.info("Uploading umpatrons.json to %s", users_bucket)
        s3.upload_file(
            OUTPUT_DIR / "umpatrons.json",
            users_bucket,
            f"UMusers-{now}.json",
        )


def upload_logs(now: str):
    """Uploads the logs after the import."""
    logs_bucket = os.getenv("LOGS_BUCKET")

    with _create_spaces_client(
        os.getenv("ACCESS_KEY"),
        os.getenv("ACCESS_SECRET"),
    ) as s3:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > 0:
            logger.info("Uploading log file to: %s", logs_bucket)
            s3.upload_file(
                LOG_FILE,
                logs_bucket,
                f"UMass_PatronTransform_{now}.log",
            )


def main():
    """The cli entrypoint to run the full import."""
    download_users()
    transform_users()

    now = datetime.now(
        ZoneInfo(os.getenv("TIMEZONE", "America/New_York")),
    ).isoformat()
    upload_users(now)
    upload_logs(now)


if __name__ == "__main__":
    main()
