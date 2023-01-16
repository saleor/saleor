import datetime
from typing import TYPE_CHECKING, Iterable, Optional, Union
from uuid import uuid4

import graphene
import pytz
from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.indexes import BTreeIndex, GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import (
    BooleanField,
    Case,
    Count,
    DateTimeField,
    Exists,
    ExpressionWrapper,
    F,
    FilteredRelation,
    JSONField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    TextField,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from django_measurement.models import MeasurementField
from django_prices.models import MoneyField
from measurement.measures import Weight
from mptt.managers import TreeManager
from mptt.models import MPTTModel
from prices import Money

from ..channel.models import Channel
from ..core.db.fields import SanitizedJSONField
from ..core.models import (
    ModelWithExternalReference,
    ModelWithMetadata,
    PublishableModel,
    SortableModel,
)
from ..core.units import WeightUnits
from ..core.utils import build_absolute_uri
from ..core.utils.editorjs import clean_editor_js
from ..core.utils.translations import Translation, TranslationProxy
from ..core.weight import zero_weight
from ..discount import DiscountInfo
from ..discount.utils import calculate_discounted_price
from ..permission.enums import (
    DiscountPermissions,
    OrderPermissions,
    ProductPermissions,
    ProductTypePermissions,
)
from ..permission.utils import has_one_of_permissions
from ..seo.models import SeoModel, SeoModelTranslation
from ..tax.models import TaxClass
from . import ProductMediaTypes, ProductTypeKind

if TYPE_CHECKING:
    from decimal import Decimal

    from ..account.models import User
    from ..app.models import App

ALL_PRODUCTS_PERMISSIONS = [
    # List of permissions, where each of them allows viewing all products
    # (including unpublished).
    OrderPermissions.MANAGE_ORDERS,
    DiscountPermissions.MANAGE_DISCOUNTS,
    ProductPermissions.MANAGE_PRODUCTS,
]


class Category(ModelWithMetadata, MPTTModel, SeoModel):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)
    description_plaintext = TextField(blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )
    background_image = models.ImageField(
        upload_to="category-backgrounds", blank=True, null=True
    )
    background_image_alt = models.CharField(max_length=128, blank=True)

    objects = models.Manager()
    tree = TreeManager()  # type: ignore[django-manager-missing]
    translated = TranslationProxy()

    class Meta:
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            GinIndex(
                name="category_search_name_slug_gin",
                # `opclasses` and `fields` should be the same length
                fields=["name", "slug", "description_plaintext"],
                opclasses=["gin_trgm_ops"] * 3,
            ),
        ]

    def __str__(self) -> str:
        return self.name


class CategoryTranslation(SeoModelTranslation):
    category = models.ForeignKey(
        Category, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128, blank=True, null=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    class Meta:
        unique_together = (("language_code", "category"),)

    def __str__(self) -> str:
        return self.name if self.name else str(self.pk)

    def __repr__(self) -> str:
        class_ = type(self)
        return "%s(pk=%r, name=%r, category_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.name,
            self.category_id,
        )

    def get_translated_object_id(self):
        return "Category", self.category_id

    def get_translated_keys(self):
        translated_keys = super().get_translated_keys()
        translated_keys.update(
            {
                "name": self.name,
                "description": self.description,
            }
        )
        return translated_keys


class ProductType(ModelWithMetadata):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    kind = models.CharField(max_length=32, choices=ProductTypeKind.CHOICES)
    has_variants = models.BooleanField(default=True)
    is_shipping_required = models.BooleanField(default=True)
    is_digital = models.BooleanField(default=False)
    weight = MeasurementField(
        measurement=Weight,
        unit_choices=WeightUnits.CHOICES,
        default=zero_weight,
    )
    tax_class = models.ForeignKey(
        TaxClass,
        related_name="product_types",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta(ModelWithMetadata.Meta):
        ordering = ("slug",)
        app_label = "product"
        permissions = (
            (
                ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.codename,
                "Manage product types and attributes.",
            ),
        )
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            GinIndex(
                name="product_type_search_gin",
                # `opclasses` and `fields` should be the same length
                fields=["name", "slug"],
                opclasses=["gin_trgm_ops"] * 2,
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        class_ = type(self)
        return "<%s.%s(pk=%r, name=%r)>" % (
            class_.__module__,
            class_.__name__,
            self.pk,
            self.name,
        )


class ProductsQueryset(models.QuerySet["Product"]):
    def published(self, channel_slug: str):
        today = datetime.datetime.now(pytz.UTC)
        channels = Channel.objects.filter(
            slug=str(channel_slug), is_active=True
        ).values("id")
        channel_listings = ProductChannelListing.objects.filter(
            Q(published_at__lte=today) | Q(published_at__isnull=True),
            Exists(channels.filter(pk=OuterRef("channel_id"))),
            is_published=True,
        ).values("id")
        return self.filter(Exists(channel_listings.filter(product_id=OuterRef("pk"))))

    def not_published(self, channel_slug: str):
        today = datetime.datetime.now(pytz.UTC)
        return self.annotate_publication_info(channel_slug).filter(
            Q(published_at__gt=today) & Q(is_published=True)
            | Q(is_published=False)
            | Q(is_published__isnull=True)
        )

    def published_with_variants(self, channel_slug: str):
        published = self.published(channel_slug)
        channels = Channel.objects.filter(
            slug=str(channel_slug), is_active=True
        ).values("id")
        variant_channel_listings = ProductVariantChannelListing.objects.filter(
            Exists(channels.filter(pk=OuterRef("channel_id"))),
            price_amount__isnull=False,
        ).values("id")
        variants = ProductVariant.objects.filter(
            Exists(variant_channel_listings.filter(variant_id=OuterRef("pk")))
        )
        return published.filter(Exists(variants.filter(product_id=OuterRef("pk"))))

    def visible_to_user(self, requestor: Union["User", "App", None], channel_slug: str):
        if has_one_of_permissions(requestor, ALL_PRODUCTS_PERMISSIONS):
            if channel_slug:
                channels = Channel.objects.filter(slug=str(channel_slug)).values("id")
                channel_listings = ProductChannelListing.objects.filter(
                    Exists(channels.filter(pk=OuterRef("channel_id")))
                ).values("id")
                return self.filter(
                    Exists(channel_listings.filter(product_id=OuterRef("pk")))
                )
            return self.all()
        return self.published_with_variants(channel_slug)

    def annotate_publication_info(self, channel_slug: str):
        return self.annotate_is_published(channel_slug).annotate_published_at(
            channel_slug
        )

    def annotate_is_published(self, channel_slug: str):
        query = Subquery(
            ProductChannelListing.objects.filter(
                product_id=OuterRef("pk"), channel__slug=str(channel_slug)
            ).values_list("is_published")[:1]
        )
        return self.annotate(
            is_published=ExpressionWrapper(query, output_field=BooleanField())
        )

    def annotate_published_at(self, channel_slug: str):
        query = Subquery(
            ProductChannelListing.objects.filter(
                product_id=OuterRef("pk"), channel__slug=str(channel_slug)
            ).values_list("published_at")[:1]
        )
        return self.annotate(
            published_at=ExpressionWrapper(query, output_field=DateTimeField())
        )

    def annotate_visible_in_listings(self, channel_slug):
        query = Subquery(
            ProductChannelListing.objects.filter(
                product_id=OuterRef("pk"), channel__slug=str(channel_slug)
            ).values_list("visible_in_listings")[:1]
        )
        return self.annotate(
            visible_in_listings=ExpressionWrapper(query, output_field=BooleanField())
        )

    def sort_by_attribute(
        self, attribute_pk: Union[int, str], descending: bool = False
    ):
        """Sort a query set by the values of the given product attribute.

        :param attribute_pk: The database ID (must be a numeric) of the attribute
                             to sort by.
        :param descending: The sorting direction.
        """
        from ..attribute.models import AttributeProduct, AttributeValue

        qs: models.QuerySet = self
        # If the passed attribute ID is valid, execute the sorting
        if not (isinstance(attribute_pk, int) or attribute_pk.isnumeric()):
            return qs.annotate(
                concatenated_values_order=Value(
                    None, output_field=models.IntegerField()
                ),
                concatenated_values=Value(None, output_field=models.CharField()),
            )

        # Retrieve all the products' attribute data IDs (assignments) and
        # product types that have the given attribute associated to them
        associated_values = tuple(
            AttributeProduct.objects.filter(attribute_id=attribute_pk).values_list(
                "pk", "product_type_id"
            )
        )

        if not associated_values:
            qs = qs.annotate(
                concatenated_values_order=Value(
                    None, output_field=models.IntegerField()
                ),
                concatenated_values=Value(None, output_field=models.CharField()),
            )

        else:
            attribute_associations, product_types_associated_to_attribute = zip(
                *associated_values
            )

            qs = qs.annotate(
                # Contains to retrieve the attribute data (singular) of each product
                # Refer to `AttributeProduct`.
                filtered_attribute=FilteredRelation(
                    relation_name="attributes",
                    condition=Q(attributes__assignment_id__in=attribute_associations),
                ),
                # Implicit `GROUP BY` required for the `StringAgg` aggregation
                grouped_ids=Count("id"),
                # String aggregation of the attribute's values to efficiently sort them
                concatenated_values=Case(
                    # If the product has no association data but has
                    # the given attribute associated to its product type,
                    # then consider the concatenated values as empty (non-null).
                    When(
                        Q(product_type_id__in=product_types_associated_to_attribute)
                        & Q(filtered_attribute=None),
                        then=models.Value(""),
                    ),
                    default=StringAgg(
                        F("filtered_attribute__values__name"),
                        delimiter=",",
                        ordering=(
                            [
                                f"filtered_attribute__values__{field_name}"
                                for field_name in AttributeValue._meta.ordering or []
                            ]
                        ),
                    ),
                    output_field=models.CharField(),
                ),
                concatenated_values_order=Case(
                    # Make the products having no such attribute be last in the sorting
                    When(concatenated_values=None, then=2),
                    # Put the products having an empty attribute value at the bottom of
                    # the other products.
                    When(concatenated_values="", then=1),
                    # Put the products having an attribute value to be always at the top
                    default=0,
                    output_field=models.IntegerField(),
                ),
            )

        # Sort by concatenated_values_order then
        # Sort each group of products (0, 1, 2, ...) per attribute values
        # Sort each group of products by name,
        # if they have the same values or not values
        ordering = "-" if descending else ""
        return qs.order_by(
            f"{ordering}concatenated_values_order",
            f"{ordering}concatenated_values",
            f"{ordering}name",
        )

    def prefetched_for_webhook(self, single_object=True):
        common_fields = (
            "attributes__values",
            "attributes__assignment__attribute",
            "media",
            "variants__attributes__values",
            "variants__attributes__assignment__attribute",
            "variants__variant_media__media",
            "variants__stocks__allocations",
            "variants__channel_listings__channel",
            "channel_listings__channel",
        )
        if single_object:
            return self.prefetch_related(*common_fields)
        return self.prefetch_related("collections", "category", *common_fields)


ProductManager = models.Manager.from_queryset(ProductsQueryset)


class Product(SeoModel, ModelWithMetadata, ModelWithExternalReference):
    product_type = models.ForeignKey(
        ProductType, related_name="products", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)
    description_plaintext = TextField(blank=True)
    search_document = models.TextField(blank=True, default="")
    search_vector = SearchVectorField(blank=True, null=True)
    search_index_dirty = models.BooleanField(default=False, db_index=True)

    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    charge_taxes = models.BooleanField(default=True)
    weight = MeasurementField(
        measurement=Weight,
        unit_choices=WeightUnits.CHOICES,
        blank=True,
        null=True,
    )
    default_variant = models.OneToOneField(
        "ProductVariant",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    rating = models.FloatField(null=True, blank=True)
    tax_class = models.ForeignKey(
        TaxClass,
        related_name="products",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    objects = ProductManager()
    translated = TranslationProxy()

    class Meta:
        app_label = "product"
        ordering = ("slug",)
        permissions = (
            (ProductPermissions.MANAGE_PRODUCTS.codename, "Manage products."),
        )
        indexes = [
            GinIndex(
                name="product_search_gin",
                fields=["search_document"],
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                name="product_tsearch",
                fields=["search_vector"],
            ),
        ]
        indexes.extend(ModelWithMetadata.Meta.indexes)

    def __iter__(self):
        if not hasattr(self, "__variants"):
            setattr(self, "__variants", self.variants.all())
        return iter(getattr(self, "__variants"))

    def __repr__(self) -> str:
        class_ = type(self)
        return "<%s.%s(pk=%r, name=%r)>" % (
            class_.__module__,
            class_.__name__,
            self.pk,
            self.name,
        )

    def __str__(self) -> str:
        return self.name

    def get_first_image(self):
        all_media = self.media.all()
        images = [media for media in all_media if media.type == ProductMediaTypes.IMAGE]
        return images[0] if images else None

    @staticmethod
    def sort_by_attribute_fields() -> list:
        return ["concatenated_values_order", "concatenated_values", "name"]


class ProductTranslation(SeoModelTranslation):
    product = models.ForeignKey(
        Product, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=250, blank=True, null=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    class Meta:
        unique_together = (("language_code", "product"),)

    def __str__(self) -> str:
        return self.name if self.name else str(self.pk)

    def __repr__(self) -> str:
        class_ = type(self)
        return "%s(pk=%r, name=%r, product_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.name,
            self.product_id,
        )

    def get_translated_object_id(self):
        return "Product", self.product_id

    def get_translated_keys(self):
        translated_keys = super().get_translated_keys()
        translated_keys.update(
            {
                "name": self.name,
                "description": self.description,
            }
        )
        return translated_keys


class ProductVariantQueryset(models.QuerySet["ProductVariant"]):
    def annotate_quantities(self):
        return self.annotate(
            quantity=Coalesce(Sum("stocks__quantity"), 0),
            quantity_allocated=Coalesce(
                Sum("stocks__allocations__quantity_allocated"), 0
            ),
        )

    def available_in_channel(self, channel_slug):
        return self.filter(
            channel_listings__price_amount__isnull=False,
            channel_listings__channel__slug=str(channel_slug),
        )

    def prefetched_for_webhook(self):
        return self.prefetch_related(
            "attributes__values",
            "attributes__assignment__attribute",
            "variant_media__media",
        )


class ProductChannelListing(PublishableModel):
    product = models.ForeignKey(
        Product,
        null=False,
        blank=False,
        related_name="channel_listings",
        on_delete=models.CASCADE,
    )
    channel = models.ForeignKey(
        Channel,
        null=False,
        blank=False,
        related_name="product_listings",
        on_delete=models.CASCADE,
    )
    visible_in_listings = models.BooleanField(default=False)
    available_for_purchase_at = models.DateTimeField(blank=True, null=True)
    currency = models.CharField(max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH)
    discounted_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    discounted_price = MoneyField(
        amount_field="discounted_price_amount", currency_field="currency"
    )

    class Meta:
        unique_together = [["product", "channel"]]
        ordering = ("pk",)
        indexes = [
            models.Index(fields=["published_at"]),
            BTreeIndex(fields=["discounted_price_amount"]),
        ]

    def is_available_for_purchase(self):
        return (
            self.available_for_purchase_at is not None
            and datetime.datetime.now(pytz.UTC) >= self.available_for_purchase_at
        )


ProductVariantManager = models.Manager.from_queryset(ProductVariantQueryset)


class ProductVariant(SortableModel, ModelWithMetadata, ModelWithExternalReference):
    sku = models.CharField(max_length=255, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255, blank=True)
    product = models.ForeignKey(
        Product, related_name="variants", on_delete=models.CASCADE
    )
    media = models.ManyToManyField("ProductMedia", through="VariantMedia")
    track_inventory = models.BooleanField(default=True)
    is_preorder = models.BooleanField(default=False)
    preorder_end_date = models.DateTimeField(null=True, blank=True)
    preorder_global_threshold = models.IntegerField(blank=True, null=True)
    quantity_limit_per_customer = models.IntegerField(
        blank=True, null=True, validators=[MinValueValidator(1)]
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    weight = MeasurementField(
        measurement=Weight,
        unit_choices=WeightUnits.CHOICES,
        blank=True,
        null=True,
    )

    objects = ProductVariantManager()
    translated = TranslationProxy()

    class Meta(ModelWithMetadata.Meta):
        ordering = ("sort_order", "sku")
        app_label = "product"

    def __str__(self) -> str:
        return self.name or self.sku or f"ID:{self.pk}"

    def get_global_id(self):
        return graphene.Node.to_global_id("ProductVariant", self.id)

    def get_price(
        self,
        product: Product,
        collections: Iterable["Collection"],
        channel: Channel,
        channel_listing: "ProductVariantChannelListing",
        discounts: Optional[Iterable[DiscountInfo]] = None,
        price_override: Optional["Decimal"] = None,
    ) -> "Money":
        price = (
            channel_listing.price
            if price_override is None
            else Money(price_override, channel_listing.currency)
        )
        return calculate_discounted_price(
            product=product,
            price=price,
            discounts=discounts,
            collections=collections,
            channel=channel,
            variant_id=self.id,
        )

    def get_weight(self):
        return self.weight or self.product.weight or self.product.product_type.weight

    def is_shipping_required(self) -> bool:
        return self.product.product_type.is_shipping_required

    def is_gift_card(self) -> bool:
        return self.product.product_type.kind == ProductTypeKind.GIFT_CARD

    def is_digital(self) -> bool:
        is_digital = self.product.product_type.is_digital
        return not self.is_shipping_required() and is_digital

    def display_product(self, translated: bool = False) -> str:
        if translated:
            product = self.product.translated
            variant_display = str(self.translated)
        else:
            variant_display = str(self)
            product = self.product
        product_display = (
            f"{product} ({variant_display})" if variant_display else str(product)
        )
        return product_display

    def get_ordering_queryset(self):
        return self.product.variants.all()

    def is_preorder_active(self):
        return self.is_preorder and (
            self.preorder_end_date is None or timezone.now() <= self.preorder_end_date
        )


class ProductVariantTranslation(Translation):
    product_variant = models.ForeignKey(
        ProductVariant, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, blank=True)

    translated = TranslationProxy()

    class Meta:
        unique_together = (("language_code", "product_variant"),)

    def __repr__(self):
        class_ = type(self)
        return "%s(pk=%r, name=%r, variant_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.name,
            self.product_variant_id,
        )

    def __str__(self):
        return self.name or str(self.product_variant)

    def get_translated_object_id(self):
        return "ProductVariant", self.product_variant_id

    def get_translated_keys(self):
        return {"name": self.name}


class ProductVariantChannelListingQuerySet(
    models.QuerySet["ProductVariantChannelListing"]
):
    def annotate_preorder_quantity_allocated(self):
        return self.annotate(
            preorder_quantity_allocated=Coalesce(
                Sum("preorder_allocations__quantity"), 0
            ),
        )


ProductVariantChannelListingManager = models.Manager.from_queryset(
    ProductVariantChannelListingQuerySet
)


class ProductVariantChannelListing(models.Model):
    variant = models.ForeignKey(
        ProductVariant,
        null=False,
        blank=False,
        related_name="channel_listings",
        on_delete=models.CASCADE,
    )
    channel = models.ForeignKey(
        Channel,
        null=False,
        blank=False,
        related_name="variant_listings",
        on_delete=models.CASCADE,
    )
    currency = models.CharField(max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH)
    price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    price = MoneyField(amount_field="price_amount", currency_field="currency")

    cost_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    cost_price = MoneyField(amount_field="cost_price_amount", currency_field="currency")

    preorder_quantity_threshold = models.IntegerField(blank=True, null=True)

    objects = ProductVariantChannelListingManager()

    class Meta:
        unique_together = [["variant", "channel"]]
        ordering = ("pk",)


class DigitalContent(ModelWithMetadata):
    FILE = "file"
    TYPE_CHOICES = ((FILE, "digital_product"),)
    use_default_settings = models.BooleanField(default=True)
    automatic_fulfillment = models.BooleanField(default=False)
    content_type = models.CharField(max_length=128, default=FILE, choices=TYPE_CHOICES)
    product_variant = models.OneToOneField(
        ProductVariant, related_name="digital_content", on_delete=models.CASCADE
    )
    content_file = models.FileField(upload_to="digital_contents", blank=True)
    max_downloads = models.IntegerField(blank=True, null=True)
    url_valid_days = models.IntegerField(blank=True, null=True)

    def create_new_url(self) -> "DigitalContentUrl":
        return self.urls.create()


class DigitalContentUrl(models.Model):
    token = models.UUIDField(editable=False, unique=True)
    content = models.ForeignKey(
        DigitalContent, related_name="urls", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    download_num = models.IntegerField(default=0)
    line = models.OneToOneField(
        "order.OrderLine",
        related_name="digital_content_url",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.token:
            self.token = str(uuid4()).replace("-", "")
        super().save(force_insert, force_update, using, update_fields)

    def get_absolute_url(self) -> Optional[str]:
        url = reverse("digital-product", kwargs={"token": str(self.token)})
        return build_absolute_uri(url)


class ProductMedia(SortableModel):
    product = models.ForeignKey(
        Product,
        related_name="media",
        on_delete=models.CASCADE,
        # DEPRECATED
        null=True,
        blank=True,
    )
    image = models.ImageField(upload_to="products", blank=True, null=True)
    alt = models.CharField(max_length=128, blank=True)
    type = models.CharField(
        max_length=32,
        choices=ProductMediaTypes.CHOICES,
        default=ProductMediaTypes.IMAGE,
    )
    external_url = models.CharField(max_length=256, blank=True, null=True)
    oembed_data = JSONField(blank=True, default=dict)
    # DEPRECATED
    to_remove = models.BooleanField(default=False)

    class Meta:
        ordering = ("sort_order", "pk")
        app_label = "product"

    def get_ordering_queryset(self):
        if not self.product:
            return ProductMedia.objects.none()
        return self.product.media.all()

    @transaction.atomic
    def delete(self, *args, **kwargs):
        super(SortableModel, self).delete(*args, **kwargs)


class VariantMedia(models.Model):
    variant = models.ForeignKey(
        "ProductVariant", related_name="variant_media", on_delete=models.CASCADE
    )
    media = models.ForeignKey(
        ProductMedia, related_name="variant_media", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("variant", "media")


class CollectionProduct(SortableModel):
    collection = models.ForeignKey(
        "Collection", related_name="collectionproduct", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, related_name="collectionproduct", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("collection", "product"),)

    def get_ordering_queryset(self):
        return self.product.collectionproduct.all()


class CollectionsQueryset(models.QuerySet["Collection"]):
    def published(self, channel_slug: str):
        today = datetime.datetime.now(pytz.UTC)
        return self.filter(
            Q(channel_listings__published_at__lte=today)
            | Q(channel_listings__published_at__isnull=True),
            channel_listings__channel__slug=str(channel_slug),
            channel_listings__channel__is_active=True,
            channel_listings__is_published=True,
        )

    def visible_to_user(self, requestor: Union["User", "App", None], channel_slug: str):
        if has_one_of_permissions(requestor, ALL_PRODUCTS_PERMISSIONS):
            if channel_slug:
                return self.filter(channel_listings__channel__slug=str(channel_slug))
            return self.all()
        return self.published(channel_slug)


CollectionManager = models.Manager.from_queryset(CollectionsQueryset)


class Collection(SeoModel, ModelWithMetadata):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    products = models.ManyToManyField(
        Product,
        blank=True,
        related_name="collections",
        through=CollectionProduct,
        through_fields=("collection", "product"),
    )
    background_image = models.ImageField(
        upload_to="collection-backgrounds", blank=True, null=True
    )
    background_image_alt = models.CharField(max_length=128, blank=True)

    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    objects = CollectionManager()

    translated = TranslationProxy()

    class Meta(ModelWithMetadata.Meta):
        ordering = ("slug",)
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            GinIndex(
                name="collection_search_gin",
                # `opclasses` and `fields` should be the same length
                fields=["name", "slug"],
                opclasses=["gin_trgm_ops"] * 2,
            ),
        ]

    def __str__(self) -> str:
        return self.name


class CollectionChannelListing(PublishableModel):
    collection = models.ForeignKey(
        Collection,
        null=False,
        blank=False,
        related_name="channel_listings",
        on_delete=models.CASCADE,
    )
    channel = models.ForeignKey(
        Channel,
        null=False,
        blank=False,
        related_name="collection_listings",
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = [["collection", "channel"]]
        ordering = ("pk",)


class CollectionTranslation(SeoModelTranslation):
    collection = models.ForeignKey(
        Collection, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128, blank=True, null=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    class Meta:
        unique_together = (("language_code", "collection"),)

    def __repr__(self):
        class_ = type(self)
        return "%s(pk=%r, name=%r, collection_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.name,
            self.collection_id,
        )

    def __str__(self) -> str:
        return self.name if self.name else str(self.pk)

    def get_translated_object_id(self):
        return "Collection", self.collection_id

    def get_translated_keys(self):
        translated_keys = super().get_translated_keys()
        translated_keys.update(
            {
                "name": self.name,
                "description": self.description,
            }
        )
        return translated_keys
