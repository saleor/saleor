from django.db import models
from django.utils.translation import pgettext_lazy

from ..account.models import ServiceAccount


class Webhook(models.Model):
    service_account = models.ForeignKey(
        ServiceAccount, related_name="webhooks", on_delete=models.CASCADE
    )
    event = models.CharField("Event", max_length=128, db_index=True)
    target_url = models.URLField("Target URL", max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        permissions = (
            (
                "manage_webhooks",
                pgettext_lazy("Webhook description", "Manage webhooks"),
            ),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "event": self.event,
            "target": self.target_url,
            "service_account_name": self.service_account.name,
        }
