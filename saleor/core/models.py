import datetime
from collections.abc import Iterable
from typing import Any, TypeVar

from django.contrib.postgres.indexes import GinIndex, PostgresIndex
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.db.models import F, JSONField, Max, Q
from django.utils.crypto import get_random_string
from storages.utils import safe_join

from . import EventDeliveryStatus, JobStatus, private_storage
from .utils.json_serializer import CustomJsonEncoder


class SortableModel(models.Model):
    sort_order = models.IntegerField(editable=False, db_index=True, null=True)

    class Meta:
        abstract = True

    def get_ordering_queryset(self):
        raise NotImplementedError("Unknown ordering queryset")

    @staticmethod
    def get_max_sort_order(qs):
        existing_max = qs.aggregate(Max("sort_order"))
        existing_max = existing_max.get("sort_order__max")
        return existing_max

    def save(self, *args, **kwargs):
        if self.pk is None:
            qs = self.get_ordering_queryset()
            existing_max = self.get_max_sort_order(qs)
            self.sort_order = 0 if existing_max is None else existing_max + 1
        super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        if self.sort_order is not None:
            qs = self.get_ordering_queryset()
            qs.filter(sort_order__gt=self.sort_order).update(
                sort_order=F("sort_order") - 1
            )
        super().delete(*args, **kwargs)


T = TypeVar("T", bound="PublishableModel")


class PublishedQuerySet(models.QuerySet[T]):
    def published(self):
        today = datetime.datetime.now(tz=datetime.UTC)
        return self.filter(
            Q(published_at__lte=today) | Q(published_at__isnull=True),
            is_published=True,
        )


PublishableManager = models.Manager.from_queryset(PublishedQuerySet)


class PublishableModel(models.Model):
    published_at = models.DateTimeField(blank=True, null=True)
    is_published = models.BooleanField(default=False)

    objects: Any = PublishableManager()

    class Meta:
        abstract = True

    @property
    def is_visible(self):
        return self.is_published and (
            self.published_at is None
            or self.published_at <= datetime.datetime.now(tz=datetime.UTC)
        )


class ModelWithMetadata(models.Model):
    private_metadata = JSONField(
        blank=True, null=True, default=dict, encoder=CustomJsonEncoder
    )
    metadata = JSONField(blank=True, null=True, default=dict, encoder=CustomJsonEncoder)

    class Meta:
        indexes: list[PostgresIndex] = [
            GinIndex(fields=["private_metadata"], name="%(class)s_p_meta_idx"),
            GinIndex(fields=["metadata"], name="%(class)s_meta_idx"),
        ]
        abstract = True

    def get_value_from_private_metadata(self, key: str, default: Any = None) -> Any:
        return self.private_metadata.get(key, default)

    def store_value_in_private_metadata(self, items: dict):
        if not self.private_metadata:
            self.private_metadata = {}
        self.private_metadata.update(items)

    def clear_private_metadata(self):
        self.private_metadata = {}

    def delete_value_from_private_metadata(self, key: str):
        if key in self.private_metadata:
            del self.private_metadata[key]

    def get_value_from_metadata(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    def store_value_in_metadata(self, items: dict):
        if not self.metadata:
            self.metadata = {}
        self.metadata.update(items)

    def clear_metadata(self):
        self.metadata = {}

    def delete_value_from_metadata(self, key: str):
        if key in self.metadata:
            del self.metadata[key]


class ModelWithExternalReference(models.Model):
    external_reference = models.CharField(
        max_length=250,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
    )

    class Meta:
        abstract = True


class Job(models.Model):
    status = models.CharField(
        max_length=50, choices=JobStatus.CHOICES, default=JobStatus.PENDING
    )
    message = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class EventPayloadManager(models.Manager["EventPayload"]):
    @transaction.atomic
    def create_with_payload_file(self, payload: str) -> "EventPayload":
        obj = super().create()
        obj.save_payload_file(payload)
        return obj

    @transaction.atomic
    def bulk_create_with_payload_files(
        self, objs: Iterable["EventPayload"], payloads=Iterable[str]
    ) -> list["EventPayload"]:
        created_objs = self.bulk_create(objs)
        for obj, payload_data in zip(created_objs, payloads):
            obj.save_payload_file(payload_data, save_instance=False)
        self.bulk_update(created_objs, ["payload_file"])
        return created_objs


class EventPayload(models.Model):
    PAYLOADS_DIR = "payloads"

    payload = models.TextField(default="")
    payload_file = models.FileField(
        storage=private_storage, upload_to=PAYLOADS_DIR, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = EventPayloadManager()

    def get_payload(self):
        if self.payload_file:
            with self.payload_file.open("rb") as f:
                payload_data = f.read()
                return payload_data.decode("utf-8")
        return self.payload

    def save_payload_file(self, payload_data: str, save_instance=True):
        payload_bytes = payload_data.encode("utf-8")
        prefix = get_random_string(length=12)
        file_name = f"{self.pk}.json"
        file_path = safe_join(prefix, file_name)
        self.payload_file.save(
            file_path, ContentFile(payload_bytes), save=save_instance
        )

    def save_as_file(self):
        payload_data = self.payload
        self.payload = ""
        self.save()
        self.save_payload_file(payload_data)


class EventDelivery(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=255,
        choices=EventDeliveryStatus.CHOICES,
        default=EventDeliveryStatus.PENDING,
    )
    event_type = models.CharField(max_length=255)
    payload = models.ForeignKey(
        EventPayload, related_name="deliveries", null=True, on_delete=models.CASCADE
    )
    webhook = models.ForeignKey("webhook.Webhook", on_delete=models.CASCADE)

    class Meta:
        ordering = ("-created_at",)


class EventDeliveryAttempt(models.Model):
    delivery = models.ForeignKey(
        EventDelivery, related_name="attempts", null=True, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    task_id = models.CharField(max_length=255, null=True)
    duration = models.FloatField(null=True)
    response = models.TextField(null=True)
    response_headers = models.TextField(null=True)
    response_status_code = models.PositiveSmallIntegerField(null=True)
    request_headers = models.TextField(null=True)
    status = models.CharField(
        max_length=255,
        choices=EventDeliveryStatus.CHOICES,
        default=EventDeliveryStatus.PENDING,
    )

    class Meta:
        ordering = ("-created_at",)
