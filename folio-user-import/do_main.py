import asyncio
from folioclient import FolioClient
from folio_data_import.UserImport import UserImporter

async def import_users():
    return UserImporter(
        FolioClient(
            folio_url=os.getenv("FOLIO_URL"),
            tenant=os.getenv("FOLIO_TENANT"),
            username=os.getenv("FOLIO_USERNAME"),
            password=os.getenv("FOLIO_PASSWORD")
        ),
        UserImporter.Config(user_file="users.jsonl")
    ).do_work()

async def download_users():
    # find latest in s3
    # download to fixed location/name
    ...

async def upload_logs(results):
    # find logs
    # upload logs to s3
    ...

async def notify(results):
    # post success to slack
    ...

async def notify_error(ex):
    # post ex to slack
    ...

async def main():
    try:
        await download_users()
        results = await import_users()
        await upload_logs(results)
        await notify(results)
    except Exception as ex:
        await notify_error(ex)

if __name__ == "__main__":
    asyncio.run(main())
