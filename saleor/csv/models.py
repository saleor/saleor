from django.db import models
from django.db.models import JSONField
from django.utils import timezone

from ..account.models import User
from ..app.models import App
from ..core.models import Job
from ..core.utils.json_serializer import CustomJsonEncoder
from . import ExportEvents


class ExportFile(Job):
    user = models.ForeignKey(
        User, related_name="export_files", on_delete=models.CASCADE, null=True
    )
    app = models.ForeignKey(
        App, related_name="export_files", on_delete=models.CASCADE, null=True
    )
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
        User, related_name="export_csv_events", on_delete=models.SET_NULL, null=True
    )
    app = models.ForeignKey(
        App, related_name="export_csv_events", on_delete=models.SET_NULL, null=True
    )
