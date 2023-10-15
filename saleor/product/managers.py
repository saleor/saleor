import datetime
from typing import Union

import pytz
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
    FilteredRelation,
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
    def published(self, channel_slug: str):
        from .models import ProductChannelListing

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
        from .models import ProductVariant, ProductVariantChannelListing

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
        from .models import ALL_PRODUCTS_PERMISSIONS, ProductChannelListing

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
        from .models import ProductChannelListing

        query = Subquery(
            ProductChannelListing.objects.filter(
                product_id=OuterRef("pk"), channel__slug=str(channel_slug)
            ).values_list("is_published")[:1]
        )
        return self.annotate(
            is_published=ExpressionWrapper(query, output_field=BooleanField())
        )

    def annotate_published_at(self, channel_slug: str):
        from .models import ProductChannelListing

        query = Subquery(
            ProductChannelListing.objects.filter(
                product_id=OuterRef("pk"), channel__slug=str(channel_slug)
            ).values_list("published_at")[:1]
        )
        return self.annotate(
            published_at=ExpressionWrapper(query, output_field=DateTimeField())
        )

    def annotate_visible_in_listings(self, channel_slug):
        from .models import ProductChannelListing

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


class ProductVariantQueryset(models.QuerySet):
    def annotate_quantities(self):
        """Annotate the queryset with quantity-related fields.

        This method annotates the queryset with the following fields:
        - `quantity`: The total quantity in stock for each product variant.
        - `quantity_allocated`: The total quantity allocated from the stock
          for each product variant.
        - `available_quantity`: The available quantity for each product variant,
          which is calculated as `quantity - quantity_allocated`.
        """

        from saleor.warehouse.models import Allocation

        allocations_subquery = (
            Allocation.objects.filter(stock__product_variant=OuterRef("pk"))
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


ProductVariantManager = models.Manager.from_queryset(ProductVariantQueryset)


class ProductVariantChannelListingQuerySet(models.QuerySet):
    def annotate_preorder_quantity_allocated(self):
        return self.annotate(
            preorder_quantity_allocated=Coalesce(
                Sum("preorder_allocations__quantity"), 0
            ),
        )


ProductVariantChannelListingManager = models.Manager.from_queryset(
    ProductVariantChannelListingQuerySet
)


class CollectionsQueryset(models.QuerySet):
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
        from .models import ALL_PRODUCTS_PERMISSIONS

        if has_one_of_permissions(requestor, ALL_PRODUCTS_PERMISSIONS):
            if channel_slug:
                return self.filter(channel_listings__channel__slug=str(channel_slug))
            return self.all()
        return self.published(channel_slug)


CollectionManager = models.Manager.from_queryset(CollectionsQueryset)
