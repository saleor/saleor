from django.db import models
from django.urls import get_script_prefix
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext_lazy as _


class PageManager(models.QuerySet):
    def public(self):
        return self.filter(status=Page.PUBLIC)

    def get_available(self, allow_draft=False):
        if not allow_draft:
            return self.public()
        return self


class Page(models.Model):
    DRAFT = 'draft'
    PUBLIC = 'public'

    STATUS_CHOICES = (
        (DRAFT, _('Draft')),
        (PUBLIC, _('Public')))

    url = models.CharField(_('URL'), max_length=100, db_index=True)
    title = models.CharField(_('title'), max_length=200)
    content = models.TextField(_('content'))
    javascript = models.TextField(_('javascript'), blank=True, default='')
    meta_tags = models.CharField(_('meta tags'), max_length=255, blank=True,
                                 help_text=_('Separated by comma.'))
    meta_description = models.TextField(_('meta description'), blank=True)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    status = models.CharField(
        max_length=255, choices=STATUS_CHOICES, default=DRAFT)
    head_tags = models.TextField(
        _('head tags'), blank=True, default='',
        help_text='Meta tags to be placed in head section')

    objects = PageManager.as_manager()

    class Meta:
        ordering = ('url',)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # Handle script prefix manually because we bypass reverse()
        return iri_to_uri(get_script_prefix().rstrip('/') + self.url)


class PostAsset(models.Model):
    page = models.ForeignKey(
        Page, related_name='assets', on_delete=models.CASCADE)
    asset = models.FileField(upload_to='page', blank=False)
