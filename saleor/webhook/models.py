from django.db import models

from ..app.models import App
from ..app.validators import AppURLValidator
from ..core.utils.json_serializer import CustomJsonEncoder
from .validators import custom_headers_validator


class WebhookURLField(models.URLField):
    default_validators = [
        AppURLValidator(schemes=["http", "https", "awssqs", "gcpubsub"])
    ]


class Webhook(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    app = models.ForeignKey(App, related_name="webhooks", on_delete=models.CASCADE)
    target_url = WebhookURLField(max_length=255)
    is_active = models.BooleanField(default=True)
    secret_key = models.CharField(max_length=255, null=True, blank=True)
    subscription_query = models.TextField(null=True, blank=True)
    custom_headers = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        encoder=CustomJsonEncoder,
        validators=[custom_headers_validator],
    )

    class Meta:
        ordering = ("pk",)

    def __str__(self):
        return self.name


class WebhookEvent(models.Model):
    webhook = models.ForeignKey(
        Webhook, related_name="events", on_delete=models.CASCADE
    )
    event_type = models.CharField("Event type", max_length=128, db_index=True)

    def __repr__(self):
        return self.event_type
