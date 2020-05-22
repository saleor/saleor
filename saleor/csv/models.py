from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone

from ..account.models import User
from ..core.models import Job
from ..core.utils.json_serializer import CustomJsonEncoder
from . import ExportEvents


class ExportFile(Job):
    created_by = models.ForeignKey(User, related_name="jobs", on_delete=models.CASCADE)
    content_file = models.FileField(upload_to="export_files", null=True)


class ExportEvent(models.Model):
    """Model used to store events that happened during the export file lifecycle."""

    date = models.DateTimeField(default=timezone.now, editable=False)
    type = models.CharField(max_length=255, choices=ExportEvents.CHOICES)
    parameters = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)
    export_file = models.ForeignKey(
        ExportFile, related_name="events", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, related_name="export_csv_events", on_delete=models.CASCADE
    )
