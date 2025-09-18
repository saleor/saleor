import datetime
from typing import Union

from django.contrib.postgres.aggregates import StringAgg
from django.db import models
from django.db.models import (
    BooleanField,
    Case,
    Count,
    DateTimeField,
    Exists,
    ExpressionWrapper,
    F,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce

from ..account.models import User
from ..app.models import App
from ..channel.models import Channel
from ..permission.utils import has_one_of_permissions


class ProductsQueryset(models.QuerySet):
    """产品模型的自定义查询集。"""

    def published(self, channel: Channel):
        """返回在给定渠道中已发布的产品。

        Args:
            channel (Channel): 要筛选的渠道。

        Returns:
            QuerySet: 已发布产品的查询集。
        """
        from .models import ProductChannelListing

        if not channel.is_active:
            return self.none()
        today = datetime.datetime.now(tz=datetime.UTC)
        channel_listings = (
            ProductChannelListing.objects.using(self.db)
            .filter(
                Q(published_at__lte=today) | Q(published_at__isnull=True),
                channel_id=channel.id,
                is_published=True,
            )
            .values("id")
        )
        return self.filter(Exists(channel_listings.filter(product_id=OuterRef("pk"))))

    def not_published(self, channel: Channel):
        """返回在给定渠道中未发布的产品。

        Args:
            channel (Channel): 要筛选的渠道。

        Returns:
            QuerySet: 未发布产品的查询集。
        """
        today = datetime.datetime.now(tz=datetime.UTC)
        return self.annotate_publication_info(channel).filter(
            Q(published_at__gt=today) & Q(is_published=True)
            | Q(is_published=False)
            | Q(is_published__isnull=True)
        )

    def published_with_variants(self, channel: Channel):
        """返回在给定渠道中已发布且具有可用变体的产品。

        Args:
            channel (Channel): 要筛选的渠道。

        Returns:
            QuerySet: 已发布且有变体的产品的查询集。
        """
        from .models import ProductVariant, ProductVariantChannelListing

        if not channel.is_active:
            return self.none()
        variant_channel_listings = (
            ProductVariantChannelListing.objects.using(self.db)
            .filter(
                channel_id=channel.id,
                price_amount__isnull=False,
            )
            .values("id")
        )
        variants = ProductVariant.objects.using(self.db).filter(
            Exists(variant_channel_listings.filter(variant_id=OuterRef("pk")))
        )
        return self.published(channel).filter(
            Exists(variants.filter(product_id=OuterRef("pk")))
        )

    def visible_to_user(
        self,
        requestor: Union["User", "App", None],
        channel: Channel | None,
        limited_channel_access: bool,
    ):
        """确定哪些产品对用户可见。

        对于没有权限的用户，我们需要传递渠道来确定哪些产品对用户可见。
        对于有权限的用户，我们可以返回：
        - 如果未传递渠道且查询未限制到提供的渠道，则返回所有产品。
          (channel=None, limited_channel_access=False)
        - 如果未传递渠道且查询限制到提供的渠道，则不返回任何产品。
          (channel=None, limited_channel_access=True)
        - 如果传递了渠道且查询限制到提供的渠道，则返回分配给该渠道的所有产品。
          (channel=Channel, limited_channel_access=True)
        """
        from .models import ALL_PRODUCTS_PERMISSIONS, ProductChannelListing

        if has_one_of_permissions(requestor, ALL_PRODUCTS_PERMISSIONS):
            if limited_channel_access:
                if channel:
                    channel_listings = (
                        ProductChannelListing.objects.using(self.db)
                        .filter(channel_id=channel.id)
                        .values("id")
                    )
                    return self.filter(
                        Exists(channel_listings.filter(product_id=OuterRef("pk")))
                    )
                return self.none()
            return self.all()
        if not channel:
            return self.none()
        return self.published_with_variants(channel)

    def annotate_publication_info(self, channel: Channel):
        """为查询集添加发布信息的注解。"""
        return self.annotate_is_published(channel).annotate_published_at(channel)

    def annotate_is_published(self, channel: Channel):
        """为查询集添加 `is_published` 注解。"""
        from .models import ProductChannelListing

        query = Subquery(
            ProductChannelListing.objects.using(self.db)
            .filter(product_id=OuterRef("pk"), channel_id=channel.id)
            .values_list("is_published")[:1]
        )
        return self.annotate(
            is_published=ExpressionWrapper(query, output_field=BooleanField())
        )

    def annotate_published_at(self, channel: Channel):
        """为查询集添加 `published_at` 注解。"""
        from .models import ProductChannelListing

        query = Subquery(
            ProductChannelListing.objects.using(self.db)
            .filter(product_id=OuterRef("pk"), channel_id=channel.id)
            .values_list("published_at")[:1]
        )
        return self.annotate(
            published_at=ExpressionWrapper(query, output_field=DateTimeField())
        )

    def annotate_visible_in_listings(self, channel: Channel | None):
        """为查询集添加 `visible_in_listings` 注解。"""
        from .models import ProductChannelListing

        if not channel:
            return self.annotate(
                visible_in_listings=Value(False, output_field=BooleanField())
            )
        query = Subquery(
            ProductChannelListing.objects.using(self.db)
            .filter(product_id=OuterRef("pk"), channel_id=channel.id)
            .values_list("visible_in_listings")[:1]
        )
        return self.annotate(
            visible_in_listings=ExpressionWrapper(query, output_field=BooleanField())
        )

    def sort_by_attribute(self, attribute_pk: int | str, descending: bool = False):
        """按给定产品属性的值对查询集进行排序。

        Args:
            attribute_pk (int | str): 要排序的属性的数据库 ID（必须是数字）。
            descending (bool, optional): 排序方向。默认为 False。
        """
        from ..attribute.models import (
            AssignedProductAttributeValue,
            AttributeProduct,
            AttributeValue,
        )

        qs: models.QuerySet = self
        # If the passed attribute ID is valid, execute the sorting
        if not (isinstance(attribute_pk, int) or attribute_pk.isnumeric()):
            return qs.annotate(
                concatenated_values_order=Value(
                    None, output_field=models.IntegerField()
                ),
                concatenated_values=Value(None, output_field=models.CharField()),
            )

        qs = qs.annotate(
            # Implicit `GROUP BY` required for the `StringAgg` aggregation
            grouped_ids=Count("id"),
            # String aggregation of the attribute's values to efficiently sort them
            concatenated_values=Case(
                # If the product has no association data but has
                # the given attribute associated to its product type,
                # then consider the concatenated values as empty (non-null).
                When(
                    Exists(
                        AttributeProduct.objects.using(self.db).filter(
                            product_type_id=OuterRef("product_type_id"),
                            attribute_id=attribute_pk,
                        )
                    )
                    & ~Exists(
                        AssignedProductAttributeValue.objects.using(self.db).filter(
                            product_id=OuterRef("id"), value__attribute_id=attribute_pk
                        )
                    ),
                    then=Value(""),
                ),
                default=StringAgg(
                    F("attributevalues__value__name"),
                    filter=Q(attributevalues__value__attribute_id=attribute_pk),
                    delimiter=",",
                    ordering=(
                        [
                            f"attributevalues__value__{field_name}"
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
        """为 webhook 预取相关的字段。"""
        common_fields = (
            "media",
            "variants__attributes__values",
            "variants__attributes__assignment__attribute",
            "variants__variant_media__media",
            "variants__stocks__allocations",
            "variants__channel_listings__channel",
            "channel_listings__channel",
            "product_type__attributeproduct",
        )
        if single_object:
            return self.prefetch_related(*common_fields)
        return self.prefetch_related("collections", "category", *common_fields)


ProductManager = models.Manager.from_queryset(ProductsQueryset)


class ProductVariantQueryset(models.QuerySet):
    """产品变体模型的自定义查询集。"""

    def annotate_quantities(self):
        """为查询集添加与数量相关的字段的注解。

        此方法为查询集添加以下字段的注解：
        - `quantity`: 每个产品变体的总库存数量。
        - `quantity_allocated`: 每个产品变体从库存中分配的总数量。
        - `available_quantity`: 每个产品变体的可用数量，
          计算方式为 `quantity - quantity_allocated`。
        """

        from saleor.warehouse.models import Allocation

        allocations_subquery = (
            Allocation.objects.using(self.db)
            .filter(stock__product_variant=OuterRef("pk"))
            .values("stock__product_variant")
            .annotate(total_allocated=Coalesce(Sum("quantity_allocated"), 0))
            .values("total_allocated")
        )

        return self.annotate(
            quantity=Coalesce(Sum("stocks__quantity"), Value(0)),
            quantity_allocated=Coalesce(
                Subquery(allocations_subquery, output_field=models.IntegerField()),
                Value(0),
            ),
            available_quantity=Case(
                When(quantity_allocated=None, then=F("quantity")),
                default=F("quantity")
                - Coalesce(
                    Subquery(allocations_subquery, output_field=models.IntegerField()),
                    Value(0),
                ),
                output_field=models.IntegerField(),
            ),
        )

    def available_in_channel(self, channel: Channel | None):
        """返回在给定渠道中可用的变体。"""
        from .models import ProductVariantChannelListing

        if not channel:
            return self.none()
        channel_listings = (
            ProductVariantChannelListing.objects.using(self.db)
            .filter(price_amount__isnull=False, channel_id=channel.id)
            .values("id")
        )
        return self.filter(Exists(channel_listings.filter(variant_id=OuterRef("pk"))))

    def prefetched_for_webhook(self):
        """为 webhook 预取相关的字段。"""
        return self.prefetch_related(
            "attributes__values",
            "attributes__assignment__attribute",
            "variant_media__media",
        )

    def visible_to_user(
        self,
        requestor: Union["User", "App", None],
        channel: Channel | None,
        limited_channel_access: bool,
    ):
        """确定哪些变体对用户可见。"""
        from .models import ALL_PRODUCTS_PERMISSIONS

        # User with product permissions can see all variants. If channel is given,
        # filter variants with product channel listings for this channel.
        if has_one_of_permissions(requestor, ALL_PRODUCTS_PERMISSIONS):
            if limited_channel_access:
                if channel:
                    return self.filter(product__channel_listings__channel_id=channel.id)
                return self.none()
            return self.all()

        # If user has no permissions (customer) and channel is not given or is inactive,
        # return no variants.
        if not channel or not channel.is_active:
            return self.none()

        # If user has no permissions (customer) and channel is given, return variants
        # that:
        # - have a variant channel listing for this channel and the price is not null
        # - have a product channel listing for this channel and the product is published
        #  and visible in listings
        variants = self.filter(
            channel_listings__channel_id=channel.id,
            channel_listings__price_amount__isnull=False,
        )

        today = datetime.datetime.now(tz=datetime.UTC)
        variants = variants.filter(
            Q(product__channel_listings__published_at__lte=today)
            | Q(product__channel_listings__published_at__isnull=True),
            product__channel_listings__is_published=True,
            product__channel_listings__channel_id=channel.id,
            product__channel_listings__visible_in_listings=True,
        )
        return variants


ProductVariantManager = models.Manager.from_queryset(ProductVariantQueryset)


class ProductVariantChannelListingQuerySet(models.QuerySet):
    """产品变体渠道列表模型的自定义查询集。"""

    def annotate_preorder_quantity_allocated(self):
        """为查询集添加 `preorder_quantity_allocated` 注解。"""
        return self.annotate(
            preorder_quantity_allocated=Coalesce(
                Sum("preorder_allocations__quantity"), 0
            ),
        )


ProductVariantChannelListingManager = models.Manager.from_queryset(
    ProductVariantChannelListingQuerySet
)


class CollectionsQueryset(models.QuerySet):
    """产品系列模型的自定义查询集。"""

    def published(self, channel_slug: str):
        """返回在给定渠道中已发布的产品系列。"""
        today = datetime.datetime.now(tz=datetime.UTC)
        return self.filter(
            Q(channel_listings__published_at__lte=today)
            | Q(channel_listings__published_at__isnull=True),
            channel_listings__channel__slug=str(channel_slug),
            channel_listings__channel__is_active=True,
            channel_listings__is_published=True,
        )

    def visible_to_user(
        self, requestor: Union["User", "App", None], channel_slug: str | None
    ):
        """确定哪些产品系列对用户可见。"""
        from .models import ALL_PRODUCTS_PERMISSIONS

        if has_one_of_permissions(requestor, ALL_PRODUCTS_PERMISSIONS):
            if channel_slug:
                return self.filter(channel_listings__channel__slug=str(channel_slug))
            return self.all()
        if not channel_slug:
            return self.none()
        return self.published(channel_slug)


CollectionManager = models.Manager.from_queryset(CollectionsQueryset)
