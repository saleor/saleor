from django.conf import settings
from django.db import models
from django.db.models import JSONField  # type: ignore
from django.utils.timezone import now

from ..app.models import App
from ..core import JobStatus
from ..core.models import Job, ModelWithMetadata
from ..core.utils import build_absolute_uri
from ..core.utils.json_serializer import CustomJsonEncoder
from ..order.models import Order
from . import InvoiceEvents


class InvoiceQueryset(models.QuerySet):
    def ready(self):
        return self.filter(job__status=JobStatus.SUCCESS)


class Invoice(ModelWithMetadata, Job):
    order = models.ForeignKey(
        Order,
        related_name="invoices",
        null=True,
        on_delete=models.SET_NULL,
    )
    number = models.CharField(max_length=255, null=True)
    created = models.DateTimeField(null=True)
    external_url = models.URLField(null=True, max_length=2048)
    invoice_file = models.FileField(upload_to="invoices")

    objects = models.Manager.from_queryset(InvoiceQueryset)()

    @property
    def url(self):
        if self.invoice_file:
            return build_absolute_uri(self.invoice_file.url)
        return self.external_url

    @url.setter
    def url(self, value):
        self.external_url = value

    def update_invoice(self, number=None, url=None):
        if number is not None:
            self.number = number
        if url is not None:
            self.external_url = url


class InvoiceEvent(models.Model):
    """Model used to store events that happened during the invoice lifecycle."""

    date = models.DateTimeField(default=now, editable=False)
    type = models.CharField(max_length=255, choices=InvoiceEvents.CHOICES)
    invoice = models.ForeignKey(
        Invoice, related_name="events", blank=True, null=True, on_delete=models.SET_NULL
    )
    order = models.ForeignKey(
        Order,
        related_name="invoice_events",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    app = models.ForeignKey(App, related_name="+", on_delete=models.SET_NULL, null=True)
    parameters = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)

    class Meta:
        ordering = ("date", "pk")

    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.type!r}, user={self.user!r})"
