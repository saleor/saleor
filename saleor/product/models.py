import copy
import datetime
from collections.abc import Iterable
from decimal import Decimal
from typing import Optional
from uuid import uuid4

import graphene
from django.conf import settings
from django.contrib.postgres.indexes import BTreeIndex, GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import JSONField, TextField
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils import timezone
from django_measurement.models import MeasurementField
from measurement.measures import Weight
from mptt.managers import TreeManager
from mptt.models import MPTTModel
from prices import Money

from ..channel.models import Channel
from ..core.db.fields import MoneyField, SanitizedJSONField
from ..core.models import (
    ModelWithExternalReference,
    ModelWithMetadata,
    PublishableModel,
    SortableModel,
)
from ..core.units import WeightUnits
from ..core.utils import build_absolute_uri
from ..core.utils.editorjs import clean_editor_js
from ..core.utils.translations import Translation, get_translation
from ..core.weight import zero_weight
from ..discount.models import PromotionRule
from ..permission.enums import (
    DiscountPermissions,
    OrderPermissions,
    ProductPermissions,
    ProductTypePermissions,
)
from ..seo.models import SeoModel, SeoModelTranslationWithSlug
from ..tax.models import TaxClass
from . import ProductMediaTypes, ProductTypeKind, managers

ALL_PRODUCTS_PERMISSIONS = [
    # List of permissions, where each of them allows viewing all products
    # (including unpublished).
    OrderPermissions.MANAGE_ORDERS,
    DiscountPermissions.MANAGE_DISCOUNTS,
    ProductPermissions.MANAGE_PRODUCTS,
]


class Category(ModelWithMetadata, MPTTModel, SeoModel):
    """产品类别模型。

    用于组织产品的层次结构。

    Attributes:
        name (str): 类别名称。
        slug (str): URL友好的类别名称。
        description (SanitizedJSONField): 类别的描述（富文本）。
        description_plaintext (str): 类别的纯文本描述。
        parent (Category): 父类别。
        background_image (ImageField): 类别的背景图片。
        background_image_alt (str): 背景图片的替代文本。
    """

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)
    description_plaintext = TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )
    background_image = models.ImageField(
        upload_to="category-backgrounds", blank=True, null=True
    )
    background_image_alt = models.CharField(max_length=128, blank=True)

    objects = models.Manager()
    tree = TreeManager()  # type: ignore[django-manager-missing]

    class Meta:
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            GinIndex(
                name="category_search_name_slug_gin",
                # `opclasses` and `fields` should be the same length
                fields=["name", "slug", "description_plaintext"],
                opclasses=["gin_trgm_ops"] * 3,
            ),
            BTreeIndex(fields=["updated_at"], name="updated_at_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class CategoryTranslation(SeoModelTranslationWithSlug):
    """产品类别翻译模型。"""

    category = models.ForeignKey(
        Category, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128, blank=True, null=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["language_code", "slug"],
                name="uniq_lang_slug_categorytransl",
            ),
        ]
        unique_together = (("language_code", "category"),)

    def __str__(self) -> str:
        return self.name if self.name else str(self.pk)

    def __repr__(self) -> str:
        class_ = type(self)
        return f"{class_.__name__}(pk={self.pk!r}, name={self.name!r}, category_pk={self.category_id!r})"

    def get_translated_object_id(self):
        """返回被翻译对象的ID。"""
        return "Category", self.category_id

    def get_translated_keys(self):
        """返回一个包含已翻译字段的字典。"""
        translated_keys = super().get_translated_keys()
        translated_keys.update(
            {
                "name": self.name,
                "description": self.description,
            }
        )
        return translated_keys


class ProductType(ModelWithMetadata):
    """产品类型模型。

    用于定义产品的通用属性，例如是否需要配送、是否为电子产品等。

    Attributes:
        name (str): 产品类型的名称。
        slug (str): URL友好的产品类型名称。
        kind (str): 产品类型的种类（例如，普通产品、礼品卡）。
        has_variants (bool): 此类型的产品是否有变体。
        is_shipping_required (bool): 此类型的产品是否需要配送。
        is_digital (bool): 此类型的产品是否为电子产品。
        weight (MeasurementField): 产品类型的重量。
        tax_class (TaxClass): 与此产品类型关联的税收类别。
    """

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
        return f"<{class_.__module__}.{class_.__name__}(pk={self.pk!r}, name={self.name!r})>"


class Product(SeoModel, ModelWithMetadata, ModelWithExternalReference):
    """产品模型。

    代表一个实际销售的商品。

    Attributes:
        product_type (ProductType): 产品的类型。
        name (str): 产品的名称。
        slug (str): URL友好的产品名称。
        description (SanitizedJSONField): 产品的描述（富文本）。
        category (Category): 产品所属的类别。
        weight (MeasurementField): 产品的重量。
        default_variant (ProductVariant): 产品的默认变体。
        rating (float): 产品的评分。
        tax_class (TaxClass): 与此产品关联的税收类别。
    """

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

    objects = managers.ProductManager()

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
            GinIndex(
                name="product_gin",
                fields=["name", "slug"],
                opclasses=["gin_trgm_ops"] * 2,
            ),
            models.Index(
                fields=["category_id", "slug"],
            ),
        ]
        indexes.extend(ModelWithMetadata.Meta.indexes)

    def __iter__(self):
        if not hasattr(self, "__variants"):
            setattr(self, "__variants", self.variants.all())
        return iter(getattr(self, "__variants"))

    def __repr__(self) -> str:
        class_ = type(self)
        return f"<{class_.__module__}.{class_.__name__}(pk={self.pk!r}, name={self.name!r})>"

    def __str__(self) -> str:
        return self.name

    def get_first_image(self):
        """返回产品的第一张图片。"""
        all_media = self.media.all()
        images = [media for media in all_media if media.type == ProductMediaTypes.IMAGE]
        return images[0] if images else None

    @staticmethod
    def sort_by_attribute_fields() -> list:
        """返回用于按属性排序的字段列表。"""
        return ["concatenated_values_order", "concatenated_values", "name"]


class ProductTranslation(SeoModelTranslationWithSlug):
    """产品翻译模型。"""

    product = models.ForeignKey(
        Product, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=250, blank=True, null=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["language_code", "slug"],
                name="uniq_lang_slug_producttransl",
            ),
        ]
        unique_together = (("language_code", "product"),)

    def __str__(self) -> str:
        return self.name if self.name else str(self.pk)

    def __repr__(self) -> str:
        class_ = type(self)
        return f"{class_.__name__}(pk={self.pk!r}, name={self.name!r}, product_pk={self.product_id!r})"

    def get_translated_object_id(self):
        """返回被翻译对象的ID。"""
        return "Product", self.product_id

    def get_translated_keys(self):
        """返回一个包含已翻译字段的字典。"""
        translated_keys = super().get_translated_keys()
        translated_keys.update(
            {
                "name": self.name,
                "description": self.description,
            }
        )
        return translated_keys


class ProductChannelListing(PublishableModel):
    """产品渠道列表模型。

    将产品与特定渠道关联起来，并定义其在该渠道中的可用性和价格。

    Attributes:
        product (Product): 关联的产品。
        channel (Channel): 关联的渠道。
        visible_in_listings (bool): 产品是否在渠道列表中可见。
        available_for_purchase_at (datetime): 产品可供购买的日期和时间。
        currency (str): 价格的货币。
        discounted_price (Money): 折扣后的价格。
    """

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
    discounted_price_dirty = models.BooleanField(default=False)

    class Meta:
        unique_together = [["product", "channel"]]
        ordering = ("pk",)
        indexes = [
            models.Index(fields=["published_at"]),
            BTreeIndex(fields=["discounted_price_amount"]),
        ]

    def is_available_for_purchase(self):
        """检查产品是否可供购买。"""
        return (
            self.available_for_purchase_at is not None
            and datetime.datetime.now(tz=datetime.UTC) >= self.available_for_purchase_at
        )


class ProductVariant(SortableModel, ModelWithMetadata, ModelWithExternalReference):
    """产品变体模型。

    代表产品的特定版本（例如，特定尺寸和颜色的 T 恤）。

    Attributes:
        sku (str): 产品的库存单位 (SKU)。
        name (str): 变体的名称。
        product (Product): 此变体所属的产品。
        media (ManyToManyField): 与此变体关联的媒体文件。
        track_inventory (bool): 是否跟踪此变体的库存。
        is_preorder (bool): 此变体是否为预购商品。
        weight (MeasurementField): 变体的重量。
    """

    sku = models.CharField(max_length=255, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255, blank=True)
    product = models.ForeignKey(
        Product, related_name="variants", on_delete=models.CASCADE
    )
    media = models.ManyToManyField(
        "product.ProductMedia", through="product.VariantMedia"
    )
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

    objects = managers.ProductVariantManager()

    class Meta(ModelWithMetadata.Meta):
        ordering = ("sort_order", "sku")
        app_label = "product"

    def __str__(self) -> str:
        return self.name or self.sku or f"ID:{self.pk}"

    def get_global_id(self):
        """返回此变体的 GraphQL 全局 ID。"""
        return graphene.Node.to_global_id("ProductVariant", self.id)

    def get_base_price(
        self,
        channel_listing: "ProductVariantChannelListing",
        price_override: Optional["Decimal"] = None,
    ) -> "Money":
        """在应用促销折扣之前返回基础变体价格。"""
        return (
            channel_listing.price
            if price_override is None
            else Money(price_override, channel_listing.currency)
        )

    def get_price(
        self,
        channel_listing: "ProductVariantChannelListing",
        price_override: Optional["Decimal"] = None,
        promotion_rules: Iterable["PromotionRule"] | None = None,
    ) -> "Money":
        """返回应用了促销活动的变体折扣价。

        如果提供了自定义价格，则返回应用了此变体有效促销规则折扣的价格。
        """
        from ..discount.utils.promotion import calculate_discounted_price_for_rules

        if price_override is None:
            return channel_listing.discounted_price or channel_listing.price
        price: Money = self.get_base_price(channel_listing, price_override)
        rules = promotion_rules or []
        return calculate_discounted_price_for_rules(
            price=price, rules=rules, currency=channel_listing.currency
        )

    def get_prior_price_amount(
        self,
        channel_listing: Optional["ProductVariantChannelListing"],
    ) -> Decimal | None:
        """返回变体之前的价格金额。"""
        if channel_listing is None or channel_listing.prior_price is None:
            return None

        return channel_listing.prior_price.amount

    def get_weight(self):
        """返回变体的重量。"""
        return self.weight or self.product.weight or self.product.product_type.weight

    def is_shipping_required(self) -> bool:
        """检查此变体是否需要配送。"""
        return self.product.product_type.is_shipping_required

    def is_gift_card(self) -> bool:
        """检查此变体是否为礼品卡。"""
        return self.product.product_type.kind == ProductTypeKind.GIFT_CARD

    def is_digital(self) -> bool:
        """检查此变体是否为电子产品。"""
        is_digital = self.product.product_type.is_digital
        return not self.is_shipping_required() and is_digital

    def display_product(self, translated: bool = False) -> str:
        """返回产品的显示名称，包括变体信息。"""
        if translated:
            product = get_translation(self.product).name or ""
            variant_display = get_translation(self).name
        else:
            variant_display = str(self)
            product = self.product
        product_display = (
            f"{product} ({variant_display})" if variant_display else str(product)
        )
        return product_display

    def get_ordering_queryset(self):
        """返回用于排序的查询集。"""
        return self.product.variants.all()

    def is_preorder_active(self):
        """检查预购是否有效。"""
        return self.is_preorder and (
            self.preorder_end_date is None or timezone.now() <= self.preorder_end_date
        )

    @property
    def comparison_fields(self):
        """返回用于比较的字段列表。"""
        return [
            "sku",
            "name",
            "track_inventory",
            "is_preorder",
            "quantity_limit_per_customer",
            "weight",
            "external_reference",
            "metadata",
            "private_metadata",
            "preorder_end_date",
            "preorder_global_threshold",
        ]

    def serialize_for_comparison(self):
        """序列化用于比较的变体数据。"""
        return copy.deepcopy(model_to_dict(self, fields=self.comparison_fields))


class ProductVariantTranslation(Translation):
    """产品变体翻译模型。"""

    product_variant = models.ForeignKey(
        ProductVariant, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (("language_code", "product_variant"),)

    def __repr__(self):
        class_ = type(self)
        return f"{class_.__name__}(pk={self.pk!r}, name={self.name!r}, variant_pk={self.product_variant_id!r})"

    def __str__(self):
        return self.name or str(self.product_variant)

    def get_translated_object_id(self):
        """返回被翻译对象的ID。"""
        return "ProductVariant", self.product_variant_id

    def get_translated_keys(self):
        """返回一个包含已翻译字段的字典。"""
        return {"name": self.name}


class ProductVariantChannelListing(models.Model):
    """产品变体渠道列表模型。

    将产品变体与特定渠道关联起来，并定义其在该渠道中的价格和成本。

    Attributes:
        variant (ProductVariant): 关联的产品变体。
        channel (Channel): 关联的渠道。
        currency (str): 价格的货币。
        price (Money): 变体在该渠道中的价格。
        cost_price (Money): 变体在该渠道中的成本价。
        prior_price (Money): 变体之前的价格。
    """

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

    prior_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    prior_price = MoneyField(
        amount_field="prior_price_amount", currency_field="currency"
    )

    discounted_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    discounted_price = MoneyField(
        amount_field="discounted_price_amount", currency_field="currency"
    )
    promotion_rules = models.ManyToManyField(
        PromotionRule,
        help_text=("Promotion rules that were included in the discounted price."),
        through="product.VariantChannelListingPromotionRule",
        blank=True,
    )

    preorder_quantity_threshold = models.IntegerField(blank=True, null=True)

    objects = managers.ProductVariantChannelListingManager()

    class Meta:
        unique_together = [["variant", "channel"]]
        ordering = ("pk",)
        indexes = [
            GinIndex(fields=["price_amount", "channel_id"]),
        ]


class VariantChannelListingPromotionRule(models.Model):
    """变体渠道列表促销规则模型。

    将变体渠道列表与促销规则关联起来，并存储折扣金额。

    Attributes:
        variant_channel_listing (ProductVariantChannelListing): 关联的变体渠道列表。
        promotion_rule (PromotionRule): 关联的促销规则。
        discount_amount (Decimal): 折扣金额。
        currency (str): 折扣的货币。
    """

    variant_channel_listing = models.ForeignKey(
        ProductVariantChannelListing,
        related_name="variantlistingpromotionrule",
        on_delete=models.CASCADE,
    )
    promotion_rule = models.ForeignKey(
        PromotionRule,
        related_name="variantlistingpromotionrule",
        on_delete=models.CASCADE,
    )
    discount_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    discount = MoneyField(amount_field="discount_amount", currency_field="currency")
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )

    class Meta:
        unique_together = [["variant_channel_listing", "promotion_rule"]]


class DigitalContent(ModelWithMetadata):
    """电子内容模型。

    代表可供下载的电子产品。

    Attributes:
        use_default_settings (bool): 是否使用默认设置。
        automatic_fulfillment (bool): 是否自动履行。
        product_variant (ProductVariant): 关联的产品变体。
        content_file (FileField): 内容文件。
        max_downloads (int): 最大下载次数。
        url_valid_days (int): URL 有效天数。
    """

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
        """创建一个新的下载 URL。"""
        return self.urls.create()


class DigitalContentUrl(models.Model):
    """电子内容 URL 模型。

    代表一个用于下载电子内容的唯一 URL。

    Attributes:
        token (UUIDField): 用于访问 URL 的唯一令牌。
        content (DigitalContent): 关联的电子内容。
        created_at (datetime): URL 的创建日期。
        download_num (int): 下载次数。
        line (OrderLine): 关联的订单行。
    """

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

    def get_absolute_url(self) -> str | None:
        """返回此下载 URL 的绝对 URL。"""
        url = reverse("digital-product", kwargs={"token": str(self.token)})
        return build_absolute_uri(url)


class ProductMedia(SortableModel, ModelWithMetadata):
    """产品媒体模型。

    代表产品的图片或视频。

    Attributes:
        product (Product): 关联的产品。
        image (ImageField): 图片文件。
        alt (str): 图片的替代文本。
        type (str): 媒体类型（图片或视频）。
        external_url (str): 外部视频的 URL。
        oembed_data (JSONField): oEmbed 数据。
    """

    product = models.ForeignKey(
        Product,
        related_name="media",
        on_delete=models.CASCADE,
        # DEPRECATED
        null=True,
        blank=True,
    )
    image = models.ImageField(upload_to="products", blank=True, null=True)
    alt = models.CharField(max_length=250, blank=True)
    type = models.CharField(
        max_length=32,
        choices=ProductMediaTypes.CHOICES,
        default=ProductMediaTypes.IMAGE,
    )
    external_url = models.CharField(max_length=256, blank=True, null=True)
    oembed_data = JSONField(blank=True, default=dict)
    # DEPRECATED
    to_remove = models.BooleanField(default=False)

    class Meta(ModelWithMetadata.Meta):
        ordering = ("sort_order", "pk")
        app_label = "product"

    def get_ordering_queryset(self):
        """返回用于排序的查询集。"""
        if not self.product:
            return ProductMedia.objects.none()
        return self.product.media.all()

    @transaction.atomic
    def delete(self, *args, **kwargs):
        super(SortableModel, self).delete(*args, **kwargs)


class VariantMedia(models.Model):
    """变体媒体模型。

    将产品变体与产品媒体关联起来。
    """

    variant = models.ForeignKey(
        "ProductVariant", related_name="variant_media", on_delete=models.CASCADE
    )
    media = models.ForeignKey(
        ProductMedia, related_name="variant_media", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("variant", "media")


class CollectionProduct(SortableModel):
    """产品系列关联模型。"""

    collection = models.ForeignKey(
        "Collection", related_name="collectionproduct", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, related_name="collectionproduct", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("collection", "product"),)

    def get_ordering_queryset(self):
        """返回用于排序的查询集。"""
        return self.product.collectionproduct.all()


class Collection(SeoModel, ModelWithMetadata):
    """产品系列模型。

    用于将产品分组到系列中。

    Attributes:
        name (str): 系列的名称。
        slug (str): URL友好的系列名称。
        products (ManyToManyField): 系列中的产品。
        background_image (ImageField): 系列的背景图片。
        background_image_alt (str): 背景图片的替代文本。
        description (SanitizedJSONField): 系列的描述（富文本）。
    """

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

    objects = managers.CollectionManager()

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
    """产品系列渠道列表模型。

    将产品系列与特定渠道关联起来，并定义其在该渠道中的可用性。
    """

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


class CollectionTranslation(SeoModelTranslationWithSlug):
    """产品系列翻译模型。"""

    collection = models.ForeignKey(
        Collection, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128, blank=True, null=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["language_code", "slug"],
                name="uniq_lang_slug_collectiontransl",
            ),
        ]
        unique_together = (("language_code", "collection"),)

    def __repr__(self):
        class_ = type(self)
        return f"{class_.__name__}(pk={self.pk!r}, name={self.name!r}, collection_pk={self.collection_id!r})"

    def __str__(self) -> str:
        return self.name if self.name else str(self.pk)

    def get_translated_object_id(self):
        """返回被翻译对象的ID。"""
        return "Collection", self.collection_id

    def get_translated_keys(self):
        """返回一个包含已翻译字段的字典。"""
        translated_keys = super().get_translated_keys()
        translated_keys.update(
            {
                "name": self.name,
                "description": self.description,
            }
        )
        return translated_keys
