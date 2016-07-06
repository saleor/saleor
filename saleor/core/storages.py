from django.conf import settings
from storages.backends.s3boto import S3BotoStorage


class S3MediaStorage(S3BotoStorage):
    def __init__(self, *args, **kwargs):
        self.bucket_name = settings.AWS_MEDIA_BUCKET_NAME
        super(S3MediaStorage, self).__init__(*args, **kwargs)
