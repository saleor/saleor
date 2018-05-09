from django.conf import settings
from django.db import models
from django.db.models import F, Max


class BaseNote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        on_delete=models.SET_NULL)
    date = models.DateTimeField(db_index=True, auto_now_add=True)
    content = models.TextField()
    is_public = models.BooleanField(default=True)

    class Meta:
        abstract = True


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
