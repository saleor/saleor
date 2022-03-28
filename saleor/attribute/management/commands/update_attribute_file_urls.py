import logging
import re
from urllib.parse import urlparse

from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ....core.storages import S3MediaStorage
from ...models import AttributeValue

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Move all attributes file to `file_upload` directory on s3 storage."

    def handle(self, *args, **options):
        storage = S3MediaStorage()

        if not storage.bucket_name:
            raise CommandError("No s3 bucket detected.")

        values = AttributeValue.objects.filter(file_url__isnull=False)
        directory = "file_upload"
        for value in values:
            file_url = value.file_url
            if not file_url or file_url.startswith(directory):
                continue
            file_name = re.sub(f"^{settings.MEDIA_URL}", "", urlparse(file_url).path)
            new_file_name = storage._clean_name(rf"{directory}/{file_name}")
            new_file_url = storage._normalize_name(new_file_name)
            old_file_url = storage._normalize_name(storage._clean_name(file_name))
            try:
                storage.bucket.Object(new_file_url).copy_from(
                    CopySource={
                        "Bucket": storage.bucket_name,
                        "Key": old_file_url,
                    }
                )
            except ClientError as exc:
                if exc.response["Error"]["Code"] == "NoSuchKey":
                    logger.info(f"No object found: {old_file_url}")
                else:
                    raise
            else:
                storage.bucket.Object(old_file_url).delete()
                logger.info(f"File {old_file_url} moved to {new_file_url}.")

                value.file_url = new_file_name
                value.save(update_fields=["file_url"])
                logger.info(
                    f"File url for AttributeValue {value} with id {value.id} "
                    "has been updated."
                )
