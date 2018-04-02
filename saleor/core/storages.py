from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class S3MediaStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        self.bucket_name = settings.AWS_MEDIA_BUCKET_NAME

        if settings.AWS_MEDIA_CUSTOM_DOMAIN:
            self.custom_domain = settings.AWS_MEDIA_CUSTOM_DOMAIN
        super().__init__(*args, **kwargs)
