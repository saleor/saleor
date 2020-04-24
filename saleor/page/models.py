from django.db import models
from draftjs_sanitizer import clean_draft_js

from ..core.db.fields import SanitizedJSONField
from ..core.models import PublishableModel, PublishedQuerySet
from ..core.permissions import PagePermissions
from ..core.utils.translations import TranslationProxy
from ..seo.models import SeoModel, SeoModelTranslation


class PagePublishedQuerySet(PublishedQuerySet):
    @staticmethod
    def user_has_access_to_all(user):
        return user.is_active and user.has_perm(PagePermissions.MANAGE_PAGES)


class Page(SeoModel, PublishableModel):
    slug = models.SlugField(unique=True, max_length=255)
    title = models.CharField(max_length=250)
    content = models.TextField(blank=True)
    content_json = SanitizedJSONField(
        blank=True, default=dict, sanitizer=clean_draft_js
    )
    created = models.DateTimeField(auto_now_add=True)

    objects = PagePublishedQuerySet.as_manager()
    translated = TranslationProxy()

    class Meta:
        ordering = ("slug",)
        permissions = ((PagePermissions.MANAGE_PAGES.codename, "Manage pages."),)

    def __str__(self):
        return self.title


class PageTranslation(SeoModelTranslation):
    language_code = models.CharField(max_length=10)
    page = models.ForeignKey(
        Page, related_name="translations", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    content_json = SanitizedJSONField(
        blank=True, default=dict, sanitizer=clean_draft_js
    )

    class Meta:
        ordering = ("language_code", "page")
        unique_together = (("language_code", "page"),)

    def __repr__(self):
        class_ = type(self)
        return "%s(pk=%r, title=%r, page_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.title,
            self.page_id,
        )

    def __str__(self):
        return self.title
