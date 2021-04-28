from django.db import models

from ..core.db.fields import SanitizedJSONField
from ..core.models import ModelWithMetadata, PublishableModel, SortableModel
from ..core.permissions import PagePermissions, PageTypePermissions
from ..core.utils.editorjs import clean_editor_js
from ..core.utils.translations import TranslationProxy
from ..seo.models import SeoModel, SeoModelTranslation
from versatileimagefield.fields import PPOIField, VersatileImageField
from ..product import ProductMediaTypes


class Page(ModelWithMetadata, SeoModel, PublishableModel):
    slug = models.SlugField(unique=True, max_length=255)
    title = models.CharField(max_length=250)
    page_type = models.ForeignKey(
        "PageType", related_name="pages", on_delete=models.CASCADE
    )
    content = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)
    created = models.DateTimeField(auto_now_add=True)

    translated = TranslationProxy()

    class Meta(ModelWithMetadata.Meta):
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
    content = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    class Meta:
        ordering = ("language_code", "page", "pk")
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

class PageMedia(SortableModel):
    page = models.ForeignKey(Page, related_name="media", on_delete=models.CASCADE)
    image = VersatileImageField(
        upload_to="pages", ppoi_field="ppoi", blank=True, null=True
    )
    ppoi = PPOIField()
    alt = models.CharField(max_length=128, blank=True)
    type = models.CharField(
        max_length=32,
        choices=ProductMediaTypes.CHOICES,
        default=ProductMediaTypes.IMAGE,
    )

    class Meta:
        ordering = ("sort_order", "pk")
        app_label = "page"

    def get_ordering_queryset(self):
        return self.page.media.all()