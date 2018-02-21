from django.db import models
from django.urls import reverse
from django.core.validators import validate_slug

from . import PageStatus


class PageManager(models.QuerySet):
    def public(self):
        return self.filter(status=PageStatus.PUBLIC)

    def get_available(self, allow_draft=False):
        if not allow_draft:
            return self.public()
        return self


class Page(models.Model):
    url = models.CharField(
        max_length=100, db_index=True, validators=[validate_slug])
    title = models.CharField(max_length=200)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=255, choices=PageStatus.CHOICES, default=PageStatus.DRAFT)

    objects = PageManager.as_manager()

    class Meta:
        ordering = ('url',)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('page:details', kwargs={'url': self.url})

    def is_public(self):
        return self.status == PageStatus.PUBLIC

    def save(self, *args, **kwargs):
        """
        Make sure url is not being written to database with uppercase.
        """
        self.url = self.url.lower()
        return super(Page, self).save(*args, **kwargs)


class PostAsset(models.Model):
    page = models.ForeignKey(
        Page, related_name='assets', on_delete=models.CASCADE)
    asset = models.FileField(upload_to='page', blank=False)
