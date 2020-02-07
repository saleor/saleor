import datetime

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import F, Max, Q

from .permissions import ProductPermissions
from .utils.json_serializer import CustomJsonEncoder


class SortableModel(models.Model):
    sort_order = models.IntegerField(editable=False, db_index=True, null=True)

    class Meta:
        abstract = True

    def get_ordering_queryset(self):
        raise NotImplementedError("Unknown ordering queryset")

    def get_max_sort_order(self, qs):
        existing_max = qs.aggregate(Max("sort_order"))
        existing_max = existing_max.get("sort_order__max")
        return existing_max

    def save(self, *args, **kwargs):
        if self.pk is None:
            qs = self.get_ordering_queryset()
            existing_max = self.get_max_sort_order(qs)
            self.sort_order = 0 if existing_max is None else existing_max + 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.sort_order is not None:
            qs = self.get_ordering_queryset()
            qs.filter(sort_order__gt=self.sort_order).update(
                sort_order=F("sort_order") - 1
            )
        super().delete(*args, **kwargs)


class PublishedQuerySet(models.QuerySet):
    def published(self):
        today = datetime.date.today()
        return self.filter(
            Q(publication_date__lte=today) | Q(publication_date__isnull=True),
            is_published=True,
        )

    @staticmethod
    def user_has_access_to_all(user):
        return user.is_active and user.has_perm(ProductPermissions.MANAGE_PRODUCTS)

    def visible_to_user(self, user):
        if self.user_has_access_to_all(user):
            return self.all()
        return self.published()


class PublishableModel(models.Model):
    publication_date = models.DateField(blank=True, null=True)
    is_published = models.BooleanField(default=False)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        abstract = True

    @property
    def is_visible(self):
        return self.is_published and (
            self.publication_date is None
            or self.publication_date < datetime.date.today()
        )


class ModelWithMetadata(models.Model):
    private_meta = JSONField(
        blank=True, null=True, default=dict, encoder=CustomJsonEncoder
    )
    meta = JSONField(blank=True, null=True, default=dict, encoder=CustomJsonEncoder)

    class Meta:
        abstract = True

    def get_private_meta(self, key: str):
        return self.private_meta.get(key, None)

    def store_private_meta(self, items: dict):
        if not self.private_meta:
            self.private_meta = {}
        self.private_meta.update(items)

    def clear_private_meta(self):
        self.private_meta = {}

    def delete_private_meta(self, key: str):
        if key in self.private_meta:
            del self.private_meta[key]

    def get_meta(self, key: str):
        return self.meta.get(key, None)

    def store_meta(self, items: dict):
        if not self.meta:
            self.meta = {}
        self.meta.update(items)

    def clear_meta(self):
        self.meta = {}

    def delete_meta(self, key: str):
        if key in self.meta:
            del self.meta[key]
