from typing import TYPE_CHECKING, Union

from django.contrib.postgres.indexes import GinIndex
from django.db import models

from ..core.db.fields import SanitizedJSONField
from ..core.models import ModelWithMetadata, PublishableModel, PublishedQuerySet
from ..core.utils.editorjs import clean_editor_js
from ..permission.enums import PagePermissions, PageTypePermissions
from ..seo.models import SeoModel, SeoModelTranslation

if TYPE_CHECKING:
    from ..account.models import User
    from ..app.models import App


class PageQueryset(PublishedQuerySet):
    def visible_to_user(self, requestor: Union["App", "User", None]):
        if requestor and requestor.has_perm(PagePermissions.MANAGE_PAGES):
            return self.all()
        return self.published()


PageManager = models.Manager.from_queryset(PageQueryset)


class Page(ModelWithMetadata, SeoModel, PublishableModel):
    slug = models.SlugField(unique=True, max_length=255)
    title = models.CharField(max_length=250)
    page_type = models.ForeignKey(
        "PageType", related_name="pages", on_delete=models.CASCADE
    )
    content = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = PageManager()  # type: ignore[assignment,misc]

    class Meta(ModelWithMetadata.Meta):
        ordering = ("slug",)
        permissions = ((PagePermissions.MANAGE_PAGES.codename, "Manage pages."),)
        indexes = [*ModelWithMetadata.Meta.indexes, GinIndex(fields=["title", "slug"])]

    def __str__(self):
        return self.title


class PageTranslation(SeoModelTranslation):
    page = models.ForeignKey(
        Page, related_name="translations", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    content = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    class Meta:
        ordering = ("language_code", "page", "pk")
        unique_together = (("language_code", "page"),)

    def __repr__(self):
        class_ = type(self)
        return f"{class_.__name__}(pk={self.pk!r}, title={self.title!r}, page_pk={self.page_id!r})"

    def __str__(self):
        return self.title if self.title else str(self.pk)

    def get_translated_object_id(self):
        return "Page", self.page_id

    def get_translated_keys(self):
        translated_keys = super().get_translated_keys()
        translated_keys.update(
            {
                "title": self.title,
                "content": self.content,
            }
        )
        return translated_keys


class PageType(ModelWithMetadata):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)

    class Meta(ModelWithMetadata.Meta):
        ordering = ("slug",)
        permissions = (
            (
                PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES.codename,
                "Manage page types and attributes.",
            ),
        )
        indexes = [*ModelWithMetadata.Meta.indexes, GinIndex(fields=["name", "slug"])]
