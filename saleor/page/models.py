import datetime

from django.core.validators import validate_slug
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import pgettext_lazy


class PageQuerySet(models.QuerySet):
    def public(self):
        today = datetime.date.today()
        return self.filter(
            Q(is_visible=True),
            Q(available_on__lte=today) | Q(available_on__isnull=True))


class Page(models.Model):
    url = models.CharField(
        max_length=100, db_index=True, validators=[validate_slug])
    title = models.CharField(max_length=200)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=False)
    available_on = models.DateField(blank=True, null=True)

    objects = PageQuerySet.as_manager()

    class Meta:
        ordering = ('url',)
        permissions = (
            ('view_page',
             pgettext_lazy('Permission description', 'Can view pages')),
            ('edit_page',
             pgettext_lazy('Permission description', 'Can edit pages')))

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('page:details', kwargs={'url': self.url})
