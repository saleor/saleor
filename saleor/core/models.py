import datetime

from django.db import models
from django.db.models import F, Max, Q


class _BaseSortableModel(models.Model):
    class Meta:
        abstract = True

    def get_ordering_queryset(self):
        raise NotImplementedError("Unknown ordering queryset")

    @property
    def _sort_order_field_name(self):
        return "sort_order"

    @property
    def _sort_order(self):
        return getattr(self, self._sort_order_field_name)

    @_sort_order.setter
    def _sort_order(self, value):
        setattr(self, self._sort_order_field_name, value)

    def _get_max_sort_order(self, qs):
        existing_max = qs.aggregate(Max(self._sort_order_field_name))
        existing_max = existing_max.get(f"{self._sort_order_field_name}__max")
        return existing_max

    def get_max_sort_order(self):
        return self._get_max_sort_order(self.get_ordering_queryset())

    def save(self, *args, **kwargs):
        if self._sort_order is None:
            qs = self.get_ordering_queryset()
            existing_max = self._get_max_sort_order(qs)
            self._sort_order = 0 if existing_max is None else existing_max + 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        qs = self.get_ordering_queryset()
        qs.filter(**{f"{self._sort_order_field_name}__gt": self._sort_order}).update(
            **{self._sort_order_field_name: F(self._sort_order_field_name) - 1}
        )
        super().delete(*args, **kwargs)


class SortableModel(_BaseSortableModel):
    sort_order = models.PositiveIntegerField(editable=False, db_index=True)

    class Meta:
        abstract = True


class SortableModelNullable(_BaseSortableModel):
    sort_order = models.PositiveIntegerField(editable=False, db_index=True, null=True)

    class Meta:
        abstract = True


class PublishedQuerySet(models.QuerySet):
    def published(self):
        today = datetime.date.today()
        return self.filter(
            Q(publication_date__lte=today) | Q(publication_date__isnull=True),
            is_published=True,
        )

    @staticmethod
    def user_has_access_to_all(user):
        return user.is_active and user.has_perm("product.manage_products")

    def visible_to_user(self, user):
        if self.user_has_access_to_all(user):
            return self.all()
        return self.published()

    def collection_sorted(self, user):
        qs = self.visible_to_user(user).prefetch_related(
            "collections__products__collectionproduct"
        )
        qs = qs.order_by(F("collectionproduct__sort_order").desc(nulls_last=True))
        return qs


class PublishableModel(models.Model):
    publication_date = models.DateField(blank=True, null=True)
    is_published = models.BooleanField(default=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        abstract = True

    @property
    def is_visible(self):
        return self.is_published and (
            self.publication_date is None
            or self.publication_date < datetime.date.today()
        )
