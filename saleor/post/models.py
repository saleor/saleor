from django.db import models
from django.contrib.postgres.indexes import GinIndex
from versatileimagefield.fields import PPOIField, VersatileImageField

from ..core.utils.translations import TranslationProxy
from django.conf import settings
from ..core.utils.editorjs import clean_editor_js
from ..core.db.fields import SanitizedJSONField
from ..core.models import ModelWithMetadata, SortableModel
from ..seo.models import SeoModel, SeoModelTranslation
from ..store.models import Store
from django.contrib.postgres.search import SearchVectorField
from ..product import ProductMediaTypes
from ..core.permissions import PostPermissions

class Post(ModelWithMetadata, SeoModel):
    tenant_id='store_id'
    title = models.CharField(max_length=250)
    content = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    store = models.ForeignKey(
        Store,
        related_name="posts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    search_vector = SearchVectorField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    # objects = models.Manager()
    translated = TranslationProxy()

    def __str__(self) -> str:
        return self.title

    class Meta:
        app_label = "post"
        ordering = ("pk",)
        permissions = (
            (PostPermissions.MANAGE_POSTS.codename, "Manage store post."),
        )
        indexes = [GinIndex(fields=["search_vector"])]
        indexes.extend(ModelWithMetadata.Meta.indexes)

class PostTranslation(SeoModelTranslation):
    language_code = models.CharField(max_length=10)
    post = models.ForeignKey(
        Post, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=250)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    class Meta:
        unique_together = (("language_code", "post"),)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        class_ = type(self)
        return "%s(pk=%r, name=%r, product_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.name,
            self.post_id,
        )

class PostMedia(SortableModel):
    post = models.ForeignKey(Post, related_name="media", on_delete=models.CASCADE)
    image = VersatileImageField(
        upload_to="post", ppoi_field="ppoi", blank=True, null=True
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
        app_label = "post"

    def get_ordering_queryset(self):
        return self.post.media.all()