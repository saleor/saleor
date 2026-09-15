from django.db import models, transaction
from django.db.models import JSONField

from ..core.models import ModelWithMetadata, SortableModel

# `ProductMediaTypes` and the URL limit predate the media app and stay where
# existing imports expect them.
from ..product import MEDIA_URL_CHAR_LIMIT, ProductMediaTypes
from . import ALT_CHAR_LIMIT, MediaOwnerTypes


class BaseMedia(SortableModel, ModelWithMetadata):
    """A single media item - an image or an oEmbed video - owned by one entity.

    There is one concrete model per owner kind, each with its own table and its
    own non-null foreign key to its owner. Ownership is therefore a database
    guarantee rather than an application-level convention, and a primary key is
    unambiguous within its table - which is what lets the GraphQL layer give each
    owner kind its own type and its own global ID.
    """

    # Set by every concrete subclass.
    owner_type: str
    owner_field: str

    objects = models.Manager()

    # Media of every owner shares the historical product prefix, so storage
    # cleanup and CDN rules keep working off a single path.
    image = models.ImageField(upload_to="products", blank=True, null=True)
    alt = models.CharField(max_length=ALT_CHAR_LIMIT, blank=True)
    type = models.CharField(
        max_length=32,
        choices=ProductMediaTypes.CHOICES,
        default=ProductMediaTypes.IMAGE,
    )
    external_url = models.CharField(
        max_length=MEDIA_URL_CHAR_LIMIT, blank=True, null=True
    )
    oembed_data = JSONField(blank=True, default=dict)

    class Meta(ModelWithMetadata.Meta):
        abstract = True
        ordering = ("sort_order", "pk")

    @property
    def owner(self):
        """Return the entity this media belongs to."""
        return getattr(self, self.owner_field)

    @property
    def owner_pk(self):
        """Return the primary key of the entity this media belongs to."""
        return getattr(self, f"{self.owner_field}_id")

    def get_ordering_queryset(self):
        return type(self)._default_manager.filter(
            **{f"{self.owner_field}_id": self.owner_pk}
        )

    @transaction.atomic
    def delete(self, *args, **kwargs):
        """Delete without renumbering siblings - gallery order tolerates gaps."""
        super(SortableModel, self).delete(*args, **kwargs)


class ProductMedia(BaseMedia):
    """A single media item owned by a product.

    `product` stays nullable for historical reasons: owner-less rows exist in
    deployments that predate the deletion-task refactor. They are unreachable
    through the API - every resolver filters them out - but they must not break
    a migration.
    """

    owner_type = MediaOwnerTypes.PRODUCT
    owner_field = "product"

    product = models.ForeignKey(
        "product.Product",
        related_name="media",
        on_delete=models.CASCADE,
        # DEPRECATED
        null=True,
        blank=True,
    )
    # DEPRECATED
    to_remove = models.BooleanField(default=False)

    class Meta(BaseMedia.Meta):
        # The table predates the media app and is baked into CDN-cached
        # thumbnail proxy URLs, so it keeps its original name.
        db_table = "product_productmedia"


class CategoryMedia(BaseMedia):
    owner_type = MediaOwnerTypes.CATEGORY
    owner_field = "category"

    category = models.ForeignKey(
        "product.Category", related_name="media", on_delete=models.CASCADE
    )

    class Meta(BaseMedia.Meta):
        pass


class CollectionMedia(BaseMedia):
    owner_type = MediaOwnerTypes.COLLECTION
    owner_field = "collection"

    collection = models.ForeignKey(
        "product.Collection", related_name="media", on_delete=models.CASCADE
    )

    class Meta(BaseMedia.Meta):
        pass


class PageMedia(BaseMedia):
    owner_type = MediaOwnerTypes.PAGE
    owner_field = "page"

    page = models.ForeignKey(
        "page.Page", related_name="media", on_delete=models.CASCADE
    )

    class Meta(BaseMedia.Meta):
        pass
