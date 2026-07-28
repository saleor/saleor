from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models

from ..app.models import App
from ..app.validators import AppURLValidator
from ..core.utils.json_serializer import CustomJsonEncoder
from .const import MAX_FILTERABLE_CHANNEL_SLUGS_LIMIT
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
    filterable_channel_slugs = ArrayField(
        models.CharField(max_length=255),
        blank=True,
        default=list,
        size=MAX_FILTERABLE_CHANNEL_SLUGS_LIMIT,
    )
    # blank=True is required because webhookCreate/webhookUpdate run full_clean:
    # Django's field validation rejects an unset value (None is in empty_values)
    # when blank=False, even with null=True, which would break every mutation
    # that doesn't set an identifier. Empty string stays blocked by the
    # identifier_not_blank CheckConstraint below.
    identifier = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        ordering = ("pk",)
        indexes = [
            GinIndex(
                name="filterable_channel_slugs_idx",
                fields=["filterable_channel_slugs"],
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["app", "identifier"],
                name="unique_webhook_identifier",
            ),
            models.CheckConstraint(
                condition=~models.Q(identifier=""),
                name="webhook_identifier_not_blank",
            ),
        ]

    def __str__(self):
        return self.name


class WebhookEvent(models.Model):
    webhook = models.ForeignKey(
        Webhook, related_name="events", on_delete=models.CASCADE
    )
    event_type = models.CharField("Event type", max_length=128, db_index=True)

    def __repr__(self):
        return self.event_type
