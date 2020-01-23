from django.db import models

from . import JobStatus


class Job(models.Model):
    status = models.CharField(max_length=50, choices=JobStatus.choices())
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True)
    content_file = models.FileField(upload_to="csv_files", null=True)
