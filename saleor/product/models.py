from decimal import Decimal
from typing import Iterable
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core import exceptions
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils.encoding import smart_text
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from django_measurement.models import MeasurementField
from django_prices.models import MoneyField
from django_prices.templatetags import prices_i18n
from draftjs_sanitizer import clean_draft_js
from measurement.measures import Weight
from mptt.managers import TreeManager
from mptt.models import MPTTModel
from prices import MoneyRange
from text_unidecode import unidecode
from versatileimagefield.fields import PPOIField, VersatileImageField

from ..core.exceptions import InsufficientStock
from ..core.fields import FilterableJSONBField, SanitizedJSONField
from ..core.models import (
    ModelWithMetadata,
    PublishableModel,
    PublishedQuerySet,
    SortableModel,
)
from ..core.utils import build_absolute_uri
from ..core.utils.draftjs import json_content_to_raw_text
from ..core.utils.translations import TranslationProxy
from ..core.weight import WeightUnits, zero_weight
from ..discount import DiscountInfo
from ..discount.utils import calculate_discounted_price
from ..seo.models import SeoModel, SeoModelTranslation
from . import AttributeInputType


def validate_attribute_json(value):
    for k, values in value.items():
        if not isinstance(k, str):
            raise exceptions.ValidationError(
                f"The key {k!r} should be of type str (got {type(k)})",
                params={"k": k, "values": values},
            )
        if not isinstance(values, list):
            raise exceptions.ValidationError(
                f"The values of {k!r} should be of type list (got {type(values)})",
                params={"k": k, "values": values},
            )

        for value_pk in values:
            if not isinstance(value_pk, str):
                raise exceptions.ValidationError(
                    f"The values inside {value_pk!r} should be of type str "
                    f"(got {type(value_pk)})",
                    params={"k": k, "values": values, "value_pk": value_pk},
                )


class Category(MPTTModel, ModelWithMetadata, SeoModel):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)
    description = models.TextField(blank=True)
    description_json = JSONField(blank=True, default=dict)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )
    background_image = VersatileImageField(
        upload_to="category-backgrounds", blank=True, null=True
    )
    background_image_alt = models.CharField(max_length=128, blank=True)

    objects = models.Manager()
    tree = TreeManager()
    translated = TranslationProxy()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "product:category", kwargs={"slug": self.slug, "category_id": self.id}
        )


class CategoryTranslation(SeoModelTranslation):
    language_code = models.CharField(max_length=10)
    category = models.ForeignKey(
        Category, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    description_json = JSONField(blank=True, default=dict)

    class Meta:
        unique_together = (("language_code", "category"),)

    def __str__(self):
        return self.name

    def __repr__(self):
        class_ = type(self)
        return "%s(pk=%r, name=%r, category_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.name,
            self.category_id,
        )


class ProductType(ModelWithMetadata):
    name = models.CharField(max_length=128)
    has_variants = models.BooleanField(default=True)
    is_shipping_required = models.BooleanField(default=True)
    is_digital = models.BooleanField(default=False)
    weight = MeasurementField(
        measurement=Weight, unit_choices=WeightUnits.CHOICES, default=zero_weight
    )

    class Meta:
        app_label = "product"

    def __str__(self):
        return self.name

    def __repr__(self):
        class_ = type(self)
        return "<%s.%s(pk=%r, name=%r)>" % (
            class_.__module__,
            class_.__name__,
            self.pk,
            self.name,
        )


class ProductsQueryset(PublishedQuerySet):
    def create(self, **kwargs):
        """
        Create a product.

        In the case of absent "minimal_variant_price" make it default to the "price"
        """
        if "minimal_variant_price" not in kwargs:
            kwargs["minimal_variant_price"] = kwargs.get("price")
        return super().create(**kwargs)

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        """
        Insert each of the product instances into the database.

        Make sure every product has "minimal_variant_price" set. Otherwise
        make it default to the "price".
        """
        for obj in objs:
            if obj.minimal_variant_price is None:
                obj.minimal_variant_price = obj.price
        return super().bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts
        )

    def collection_sorted(self, user):
        qs = self.visible_to_user(user).prefetch_related(
            "collections__products__collectionproduct"
        )
        qs = qs.order_by(
            F("collectionproduct__sort_order").asc(nulls_last=True),
            F("collectionproduct__id"),
        )
        return qs


class Product(SeoModel, ModelWithMetadata, PublishableModel):
    product_type = models.ForeignKey(
        ProductType, related_name="products", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    description_json = SanitizedJSONField(
        blank=True, default=dict, sanitizer=clean_draft_js
    )
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.CASCADE
    )
    price = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    minimal_variant_price = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    attributes = FilterableJSONBField(
        default=dict, blank=True, validators=[validate_attribute_json]
    )
    updated_at = models.DateTimeField(auto_now=True, null=True)
    charge_taxes = models.BooleanField(default=True)
    weight = MeasurementField(
        measurement=Weight, unit_choices=WeightUnits.CHOICES, blank=True, null=True
    )
    objects = ProductsQueryset.as_manager()
    translated = TranslationProxy()

    class Meta:
        app_label = "product"
        ordering = ("name",)
        permissions = (
            (
                "manage_products",
                pgettext_lazy("Permission description", "Manage products."),
            ),
        )

    def __iter__(self):
        if not hasattr(self, "__variants"):
            setattr(self, "__variants", self.variants.all())
        return iter(getattr(self, "__variants"))

    def __repr__(self):
        class_ = type(self)
        return "<%s.%s(pk=%r, name=%r)>" % (
            class_.__module__,
            class_.__name__,
            self.pk,
            self.name,
        )

    def __str__(self):
        return self.name

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        # Make sure the "minimal_variant_price" is set
        if self.minimal_variant_price is None:
            self.minimal_variant_price = self.price
        return super().save(force_insert, force_update, using, update_fields)

    @property
    def plain_text_description(self):
        if settings.USE_JSON_CONTENT:
            return json_content_to_raw_text(self.description_json)
        return strip_tags(self.description)

    @property
    def is_available(self):
        return self.is_visible and self.is_in_stock()

    def get_absolute_url(self):
        return reverse(
            "product:details", kwargs={"slug": self.get_slug(), "product_id": self.id}
        )

    def get_slug(self):
        return slugify(smart_text(unidecode(self.name)))

    def is_in_stock(self):
        return any(variant.is_in_stock() for variant in self)

    def get_first_image(self):
        images = list(self.images.all())
        return images[0] if images else None

    def get_price_range(self, discounts: Iterable[DiscountInfo] = None):
        if self.variants.all():
            prices = [variant.get_price(discounts) for variant in self]
            return MoneyRange(min(prices), max(prices))
        price = calculate_discounted_price(self, self.price, discounts)
        return MoneyRange(start=price, stop=price)


class ProductTranslation(SeoModelTranslation):
    language_code = models.CharField(max_length=10)
    product = models.ForeignKey(
        Product, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    description_json = SanitizedJSONField(
        blank=True, default=dict, sanitizer=clean_draft_js
    )

    class Meta:
        unique_together = (("language_code", "product"),)

    def __str__(self):
        return self.name

    def __repr__(self):
        class_ = type(self)
        return "%s(pk=%r, name=%r, product_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.name,
            self.product_id,
        )


class ProductVariantQueryset(models.QuerySet):
    def create(self, **kwargs):
        """
        Create a product's variant.

        After the creation update the "minimal_variant_price" of the product.
        """
        variant = super().create(**kwargs)
        from .tasks import update_product_minimal_variant_price_task

        update_product_minimal_variant_price_task.delay(variant.product_id)
        return variant

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        """
        Insert each of the product's variant instances into the database.

        After the creation update the "minimal_variant_price" of all the products.
        """
        variants = super().bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts
        )
        product_pks = set()
        for obj in objs:
            product_pks.add(obj.product_id)
        product_pks = list(product_pks)
        from .tasks import update_products_minimal_variant_prices_task

        update_products_minimal_variant_prices_task.delay(product_pks)
        return variants


class ProductVariant(ModelWithMetadata):
    sku = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255, blank=True)
    price_override = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    product = models.ForeignKey(
        Product, related_name="variants", on_delete=models.CASCADE
    )
    attributes = FilterableJSONBField(
        default=dict, blank=True, validators=[validate_attribute_json]
    )
    images = models.ManyToManyField("ProductImage", through="VariantImage")
    track_inventory = models.BooleanField(default=True)
    quantity = models.IntegerField(
        validators=[MinValueValidator(0)], default=Decimal(1)
    )
    quantity_allocated = models.IntegerField(
        validators=[MinValueValidator(0)], default=Decimal(0)
    )
    cost_price = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    weight = MeasurementField(
        measurement=Weight, unit_choices=WeightUnits.CHOICES, blank=True, null=True
    )

    objects = ProductVariantQueryset.as_manager()
    translated = TranslationProxy()

    class Meta:
        app_label = "product"

    def __str__(self):
        return self.name or self.sku

    @property
    def quantity_available(self):
        return max(self.quantity - self.quantity_allocated, 0)

    @property
    def is_visible(self):
        return self.product.is_visible

    @property
    def is_available(self):
        return self.product.is_available

    def check_quantity(self, quantity):
        """Check if there is at least the given quantity in stock.

        If stock handling is disabled, it simply run no check.
        """
        if self.track_inventory and quantity > self.quantity_available:
            raise InsufficientStock(self)

    @property
    def base_price(self):
        return (
            self.price_override
            if self.price_override is not None
            else self.product.price
        )

    def get_price(self, discounts: Iterable[DiscountInfo] = None):
        return calculate_discounted_price(self.product, self.base_price, discounts)

    def get_weight(self):
        return self.weight or self.product.weight or self.product.product_type.weight

    def get_absolute_url(self):
        slug = self.product.get_slug()
        product_id = self.product.id
        return reverse(
            "product:details", kwargs={"slug": slug, "product_id": product_id}
        )

    def is_shipping_required(self):
        return self.product.product_type.is_shipping_required

    def is_digital(self):
        is_digital = self.product.product_type.is_digital
        return not self.is_shipping_required() and is_digital

    def is_in_stock(self):
        return self.quantity_available > 0

    def display_product(self, translated=False):
        if translated:
            product = self.product.translated
            variant_display = str(self.translated)
        else:
            variant_display = str(self)
            product = self.product
        product_display = (
            "%s (%s)" % (product, variant_display) if variant_display else str(product)
        )
        return smart_text(product_display)

    def get_first_image(self):
        images = list(self.images.all())
        return images[0] if images else self.product.get_first_image()

    def get_ajax_label(self, discounts=None):
        price = self.get_price(discounts)
        return "%s, %s, %s" % (
            self.sku,
            self.display_product(),
            prices_i18n.amount(price),
        )


class ProductVariantTranslation(models.Model):
    language_code = models.CharField(max_length=10)
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


class DigitalContent(ModelWithMetadata):
    FILE = "file"
    TYPE_CHOICES = (
        (FILE, pgettext_lazy("File as a digital product", "digital_product")),
    )
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
    created = models.DateTimeField(auto_now_add=True)
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

    def get_absolute_url(self) -> str:
        url = reverse("product:digital-product", kwargs={"token": str(self.token)})
        return build_absolute_uri(url)


class AttributeProduct(SortableModel):
    attribute = models.ForeignKey(
        "Attribute", related_name="attributeproduct", on_delete=models.CASCADE
    )
    product_type = models.ForeignKey(
        ProductType, related_name="attributeproduct", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("attribute", "product_type"),)

    def get_ordering_queryset(self):
        return self.product_type.attributeproduct.all()


class AttributeVariant(SortableModel):
    attribute = models.ForeignKey(
        "Attribute", related_name="attributevariant", on_delete=models.CASCADE
    )
    product_type = models.ForeignKey(
        ProductType, related_name="attributevariant", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("attribute", "product_type"),)

    def get_ordering_queryset(self):
        return self.product_type.attributevariant.all()


class AttributeQuerySet(models.QuerySet):
    def get_unassigned_attributes(self, product_type_pk: int):
        return self.exclude(
            Q(attributeproduct__product_type_id=product_type_pk)
            | Q(attributevariant__product_type_id=product_type_pk)
        )

    def get_assigned_attributes(self, product_type_pk: int):
        return self.filter(
            Q(attributeproduct__product_type_id=product_type_pk)
            | Q(attributevariant__product_type_id=product_type_pk)
        )

    @staticmethod
    def user_has_access_to_all(user):
        return user.is_active and user.has_perm("product.manage_products")

    def get_public_attributes(self):
        return self.filter(visible_in_storefront=True)

    def get_visible_to_user(self, user):
        if self.user_has_access_to_all(user):
            return self.all()
        return self.get_public_attributes()

    def _get_sorted_m2m_field(self, m2m_field_name: str, asc: bool):
        sort_order_field = F(f"{m2m_field_name}__sort_order")
        id_field = F(f"{m2m_field_name}__id")
        if asc:
            sort_method = sort_order_field.asc(nulls_last=True)
            id_sort = id_field
        else:
            sort_method = sort_order_field.desc(nulls_first=True)
            id_sort = id_field.desc()

        return self.order_by(sort_method, id_sort)

    def product_attributes_sorted(self, asc=True):
        return self._get_sorted_m2m_field("attributeproduct", asc)

    def variant_attributes_sorted(self, asc=True):
        return self._get_sorted_m2m_field("attributevariant", asc)


class Attribute(ModelWithMetadata):
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=50)

    input_type = models.CharField(
        max_length=50,
        choices=AttributeInputType.CHOICES,
        default=AttributeInputType.DROPDOWN,
    )

    product_types = models.ManyToManyField(
        ProductType,
        blank=True,
        related_name="product_attributes",
        through=AttributeProduct,
        through_fields=["attribute", "product_type"],
    )
    product_variant_types = models.ManyToManyField(
        ProductType,
        blank=True,
        related_name="variant_attributes",
        through=AttributeVariant,
        through_fields=["attribute", "product_type"],
    )

    value_required = models.BooleanField(default=False, blank=True)
    is_variant_only = models.BooleanField(default=False, blank=True)
    visible_in_storefront = models.BooleanField(default=True, blank=True)

    filterable_in_storefront = models.BooleanField(default=True, blank=True)
    filterable_in_dashboard = models.BooleanField(default=True, blank=True)

    storefront_search_position = models.IntegerField(default=0, blank=True)
    available_in_grid = models.BooleanField(default=True, blank=True)

    objects = AttributeQuerySet.as_manager()
    translated = TranslationProxy()

    class Meta:
        ordering = ("storefront_search_position", "slug")

    def __str__(self):
        return self.name

    def get_formfield_name(self):
        return slugify("attribute-%s-%s" % (self.slug, self.pk), allow_unicode=True)

    def has_values(self):
        return self.values.exists()


class AttributeTranslation(models.Model):
    language_code = models.CharField(max_length=10)
    attribute = models.ForeignKey(
        Attribute, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = (("language_code", "attribute"),)

    def __repr__(self):
        class_ = type(self)
        return "%s(pk=%r, name=%r, attribute_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.name,
            self.attribute_id,
        )

    def __str__(self):
        return self.name


class AttributeValue(SortableModel):
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100, blank=True, default="")
    slug = models.SlugField(max_length=100)
    attribute = models.ForeignKey(
        Attribute, related_name="values", on_delete=models.CASCADE
    )

    translated = TranslationProxy()

    class Meta:
        ordering = ("sort_order", "id")
        unique_together = ("name", "attribute")

    def __str__(self):
        return self.name

    @property
    def input_type(self):
        return self.attribute.input_type

    def get_ordering_queryset(self):
        return self.attribute.values.all()


class AttributeValueTranslation(models.Model):
    language_code = models.CharField(max_length=10)
    attribute_value = models.ForeignKey(
        AttributeValue, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = (("language_code", "attribute_value"),)

    def __repr__(self):
        class_ = type(self)
        return "%s(pk=%r, name=%r, attribute_value_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.name,
            self.attribute_value_id,
        )

    def __str__(self):
        return self.name


class ProductImage(SortableModel):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = VersatileImageField(upload_to="products", ppoi_field="ppoi", blank=False)
    ppoi = PPOIField()
    alt = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ("sort_order",)
        app_label = "product"

    def get_ordering_queryset(self):
        return self.product.images.all()


class VariantImage(models.Model):
    variant = models.ForeignKey(
        "ProductVariant", related_name="variant_images", on_delete=models.CASCADE
    )
    image = models.ForeignKey(
        ProductImage, related_name="variant_images", on_delete=models.CASCADE
    )


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


class Collection(SeoModel, ModelWithMetadata, PublishableModel):
    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=128)
    products = models.ManyToManyField(
        Product,
        blank=True,
        related_name="collections",
        through=CollectionProduct,
        through_fields=["collection", "product"],
    )
    background_image = VersatileImageField(
        upload_to="collection-backgrounds", blank=True, null=True
    )
    background_image_alt = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    description_json = JSONField(blank=True, default=dict)

    translated = TranslationProxy()

    class Meta:
        ordering = ("slug",)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product:collection", kwargs={"pk": self.id, "slug": self.slug})


class CollectionTranslation(SeoModelTranslation):
    language_code = models.CharField(max_length=10)
    collection = models.ForeignKey(
        Collection, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    description_json = JSONField(blank=True, default=dict)

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

    def __str__(self):
        return self.name
