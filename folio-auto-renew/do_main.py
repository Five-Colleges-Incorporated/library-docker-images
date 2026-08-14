"""Entrypoint for nightly auto renewals."""

import asyncio
import logging
import os
from contextlib import closing, contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import boto3
import folio_auto_renew as far
from folioclient import FolioClient

PWD = Path.cwd()
LOG_FILE = PWD / "log"

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())

now = datetime.now(ZoneInfo(os.getenv("TIMEZONE", "America/New_York")))


async def renew_loans():
    """Renews loans using the folio-auto-renew library."""
    dry_run = os.getenv("DRY_RUN", "1") == "1"
    patron_prefixes = os.getenv("PATRON_PREFIXES", "").split(",")
    future_days = int(os.getenv("FUTURE_DAYS", "14"))

    client = FolioClient(
        os.getenv("FOLIO_URL"),
        os.getenv("FOLIO_TENANT"),
        os.getenv("FOLIO_USERNAME"),
        os.getenv("FOLIO_PASSWORD"),
    )

    logger.info("Fetching Renewals")
    renewable_loans = far.stream_loans(
        client=client,
        patron_barcode_patterns=patron_prefixes,
        due_date=now + timedelta(days=future_days),
    )

    logger.info("Renewing Loans")
    await far.renew_loans(client, renewable_loans, dry_run=dry_run)


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


def upload_logs():
    """Uploads the errors and logs after the renewal."""
    logs_bucket = os.getenv("LOGS_BUCKET")

    with _create_spaces_client(os.getenv("LOGS_KEY"), os.getenv("LOGS_SECRET")) as s3:
        log_key = f"{os.getenv('LIBRARY_NAME', 'UNKNOWN')}_{now.isoformat()}.log"
        logger.info("Uploading log file to: %s/%s", logs_bucket, log_key)
        s3.upload_file(LOG_FILE, logs_bucket, log_key)


async def main():
    """The cli entrypoint to run the renew."""
    try:
        await renew_loans()
    finally:
        upload_logs()


if __name__ == "__main__":
    asyncio.run(main())
