from django.conf import settings
from storages.backends.azure_storage import AzureStorage
from storages.backends.gcloud import GoogleCloudStorage
from storages.backends.s3boto3 import S3Boto3Storage


class S3MediaStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        self.bucket_name = settings.AWS_MEDIA_BUCKET_NAME
        self.custom_domain = settings.AWS_MEDIA_CUSTOM_DOMAIN
        super().__init__(*args, **kwargs)


class GCSMediaStorage(GoogleCloudStorage):
    def __init__(self, *args, **kwargs):
        self.bucket_name = settings.GS_MEDIA_BUCKET_NAME
        self.custom_endpoint = settings.GS_MEDIA_CUSTOM_ENDPOINT
        super().__init__(*args, **kwargs)


class AzureMediaStorage(AzureStorage):
    def __init__(self, *args, **kwargs):
        self.account_name = settings.AZURE_ACCOUNT_NAME
        self.account_key = settings.AZURE_ACCOUNT_KEY
        self.azure_container = settings.AZURE_CONTAINER
        self.azure_ssl = settings.AZURE_SSL
        self.expiration_secs = None
        super().__init__(*args, **kwargs)
