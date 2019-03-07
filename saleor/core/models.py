import datetime

from django.db import models
from django.db.models import F, Max, Q


class SortableModel(models.Model):
    sort_order = models.PositiveIntegerField(editable=False, db_index=True)

    class Meta:
        abstract = True

    def get_ordering_queryset(self):
        raise NotImplementedError('Unknown ordering queryset')

    def save(self, *args, **kwargs):
        if self.sort_order is None:
            qs = self.get_ordering_queryset()
            existing_max = qs.aggregate(Max('sort_order'))
            existing_max = existing_max.get('sort_order__max')
            self.sort_order = 0 if existing_max is None else existing_max + 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        qs = self.get_ordering_queryset()
        qs.filter(sort_order__gt=self.sort_order).update(
            sort_order=F('sort_order') - 1)
        super().delete(*args, **kwargs)


class PublishedQuerySet(models.QuerySet):

    def published(self):
        today = datetime.date.today()
        return self.filter(
            Q(publication_date__lte=today) | Q(publication_date__isnull=True),
            is_published=True)

    @staticmethod
    def user_has_access_to_all(user):
        return user.is_active and user.has_perm('product.manage_products')

    def visible_to_user(self, user):
        if self.user_has_access_to_all(user):
            return self.all()
        return self.published()


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
            or self.publication_date < datetime.date.today())
