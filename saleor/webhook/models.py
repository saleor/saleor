from django.core import validators
from django.db import models

from ..app.models import App


class WebhookURLField(models.URLField):
    default_validators = [
        validators.URLValidator(schemes=["http", "https", "awssqs", "gcpubsub"])
    ]


class Webhook(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    app = models.ForeignKey(App, related_name="webhooks", on_delete=models.CASCADE)
    target_url = WebhookURLField(max_length=255)
    is_active = models.BooleanField(default=True)
    secret_key = models.CharField(max_length=255, null=True, blank=True)


class WebhookEvent(models.Model):
    webhook = models.ForeignKey(
        Webhook, related_name="events", on_delete=models.CASCADE
    )
    event_type = models.CharField("Event type", max_length=128, db_index=True)

    def __repr__(self):
        return self.event_type
