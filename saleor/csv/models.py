from django.db import models

from ..account.models import User
from ..core.models import Job


class ExportFile(Job):
    created_by = models.ForeignKey(User, related_name="jobs", on_delete=models.CASCADE)
    content_file = models.FileField(upload_to="csv_files", null=True)
