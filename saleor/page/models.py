import datetime

from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import pgettext_lazy

from ..core.utils import build_absolute_uri
from ..core.utils.translations import TranslationProxy
from ..seo.models import SeoModel, SeoModelTranslation


class PageQuerySet(models.QuerySet):
    def public(self):
        today = datetime.date.today()
        return self.filter(
            Q(is_visible=True),
            Q(available_on__lte=today) | Q(available_on__isnull=True))


class Page(SeoModel):
    slug = models.SlugField(unique=True, max_length=100)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=False)
    available_on = models.DateField(blank=True, null=True)

    objects = PageQuerySet.as_manager()
    translated = TranslationProxy()

    class Meta:
        ordering = ('slug',)
        permissions = ((
            'manage_pages', pgettext_lazy(
                'Permission description', 'Manage pages.')),)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('page:details', kwargs={'slug': self.slug})

    def get_full_url(self):
        return build_absolute_uri(self.get_absolute_url())

    @property
    def is_published(self):
        today = datetime.date.today()
        return self.is_visible and (
            self.available_on is None or self.available_on <= today)


class PageTranslation(SeoModelTranslation):
    language_code = models.CharField(max_length=10)
    page = models.ForeignKey(
        Page, related_name='translations', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()

    class Meta:
        unique_together = (('language_code', 'page'),)

    def __repr__(self):
        class_ = type(self)
        return '%s(pk=%r, title=%r, page_pk=%r)' % (
            class_.__name__, self.pk, self.title, self.page_id)

    def __str__(self):
        return self.title
