from django.db import models
from django.utils.translation import pgettext_lazy

from ..account.models import ServiceAccount


class Webhook(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    service_account = models.ForeignKey(
        ServiceAccount, related_name="webhooks", on_delete=models.CASCADE
    )
    target_url = models.URLField(max_length=255)
    is_active = models.BooleanField(default=True)
    secret_key = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        permissions = (
            (
                "manage_webhooks",
                pgettext_lazy("Webhook description", "Manage webhooks"),
            ),
        )


class WebhookEvent(models.Model):
    webhook = models.ForeignKey(
        Webhook, related_name="events", on_delete=models.CASCADE
    )
    event_type = models.CharField("Event type", max_length=128, db_index=True)

    def __repr__(self):
        return self.event_type
