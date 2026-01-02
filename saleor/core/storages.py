from django.conf import settings
from storages.backends.azure_storage import AzureStorage as AzureBaseStorage
from storages.backends.gcloud import GoogleCloudStorage
from storages.backends.s3boto3 import S3Boto3Storage

from . import AWS_KEY


class S3MediaStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        self.bucket_name = settings.AWS_MEDIA_BUCKET_NAME
        self.custom_domain = settings.AWS_MEDIA_CUSTOM_DOMAIN
        # Using fake AWS key for testing
        if not settings.AWS_SECRET_ACCESS_KEY:
            kwargs.setdefault("aws_secret_access_key", AWS_KEY)
        super().__init__(*args, **kwargs)


class S3MediaPrivateStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        self.bucket_name = settings.AWS_MEDIA_PRIVATE_BUCKET_NAME
        self.custom_domain = None
        super().__init__(*args, **kwargs)


class GCSMediaStorage(GoogleCloudStorage):
    def __init__(self, *args, **kwargs):
        self.bucket_name = settings.GS_MEDIA_BUCKET_NAME
        self.custom_endpoint = settings.GS_MEDIA_CUSTOM_ENDPOINT
        super().__init__(*args, **kwargs)


class GCSMediaPrivateStorage(GoogleCloudStorage):
    def __init__(self, *args, **kwargs):
        self.bucket_name = settings.GS_MEDIA_PRIVATE_BUCKET_NAME
        self.custom_endpoint = None
        super().__init__(*args, **kwargs)


class AzureStorage(AzureBaseStorage):
    def __init__(self, *args, **kwargs):
        self.account_name = settings.AZURE_ACCOUNT_NAME
        self.account_key = settings.AZURE_ACCOUNT_KEY
        self.azure_ssl = settings.AZURE_SSL
        self.expiration_secs = None
        super().__init__(*args, **kwargs)


class AzureMediaStorage(AzureBaseStorage):
    def __init__(self, *args, **kwargs):
        self.azure_container = settings.AZURE_CONTAINER
        super().__init__(*args, **kwargs)


class AzureMediaPrivateStorage(AzureBaseStorage):
    def __init__(self, *args, **kwargs):
        self.azure_container = settings.AZURE_CONTAINER_PRIVATE
        super().__init__(*args, **kwargs)
