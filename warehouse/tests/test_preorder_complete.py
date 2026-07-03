from django.db.models.aggregates import Sum

from ...product.models import ProductVariantChannelListing
from ..management import deactivate_preorder_for_variant
from ..models import Allocation, PreorderAllocation, Stock


def test_deactivate_preorder_for_variant(
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
    shipping_method_channel_PLN,
):
    variant = preorder_variant_global_and_channel_threshold
    order = preorder_allocation.order_line.order
    order.shipping_method = shipping_method_channel_PLN
    order.save(update_fields=["shipping_method"])

    channel_listings_id = ProductVariantChannelListing.objects.filter(
        variant_id=variant.pk
    ).values_list("id", flat=True)
    preorder_allocations_before = PreorderAllocation.objects.filter(
        product_variant_channel_listing_id__in=channel_listings_id
    ).count()
    assert preorder_allocations_before > 0

    allocations_before = Allocation.objects.filter(
        stock__product_variant_id=variant.pk
    ).count()
    # Allocations and stocks will be created
    assert variant.stocks.count() == 0

    deactivate_preorder_for_variant(variant)

    assert (
        PreorderAllocation.objects.filter(
            product_variant_channel_listing_id__in=channel_listings_id
        ).count()
        == 0
    )
    assert (
        Allocation.objects.filter(stock__product_variant_id=variant.pk).count()
        == allocations_before + preorder_allocations_before
    )

    variant.refresh_from_db()

    stock = variant.stocks.first()
    assert (
        stock.quantity_allocated
        == stock.allocations.aggregate(Sum("quantity_allocated"))[
            "quantity_allocated__sum"
        ]
    )
    assert variant.is_preorder is False
    assert variant.preorder_global_threshold is None
    assert variant.preorder_end_date is None

    channel_listings = ProductVariantChannelListing.objects.filter(
        variant_id=variant.pk
    )
    for channel_listing in channel_listings:
        assert channel_listing.preorder_quantity_threshold is None


def test_deactivate_preorder_for_variant_order_without_shipping_method(
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
):
    """When order has no shiping method set, use warehouse based on country from address."""
    variant = preorder_variant_global_and_channel_threshold
    order = preorder_allocation.order_line.order
    assert order.shipping_method is None

    channel_listings_id = ProductVariantChannelListing.objects.filter(
        variant_id=variant.pk
    ).values_list("id", flat=True)
    preorder_allocations_before = PreorderAllocation.objects.filter(
        product_variant_channel_listing_id__in=channel_listings_id
    ).count()
    assert preorder_allocations_before > 0

    allocations_before = Allocation.objects.filter(
        stock__product_variant_id=variant.pk
    ).count()

    deactivate_preorder_for_variant(variant)

    assert (
        PreorderAllocation.objects.filter(
            product_variant_channel_listing_id__in=channel_listings_id
        ).count()
        == 0
    )
    assert (
        Allocation.objects.filter(stock__product_variant_id=variant.pk).count()
        == allocations_before + preorder_allocations_before
    )


def test_deactivate_preorder_for_variant_existing_stock(
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
    shipping_method_channel_PLN,
    warehouse,
):
    variant = preorder_variant_global_and_channel_threshold
    order = preorder_allocation.order_line.order
    order.shipping_method = shipping_method_channel_PLN
    order.save(update_fields=["shipping_method"])

    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=0
    )

    channel_listings_id = ProductVariantChannelListing.objects.filter(
        variant_id=variant.pk
    ).values_list("id", flat=True)
    preorder_allocations_before = PreorderAllocation.objects.filter(
        product_variant_channel_listing_id__in=channel_listings_id
    ).count()
    assert preorder_allocations_before > 0

    allocations_before = Allocation.objects.filter(
        stock__product_variant_id=variant.pk
    ).count()

    # Existing stock will be used
    assert variant.stocks.count() > 0

    deactivate_preorder_for_variant(variant)
    stock.refresh_from_db()

    assert (
        PreorderAllocation.objects.filter(
            product_variant_channel_listing_id__in=channel_listings_id
        ).count()
        == 0
    )
    assert (
        Allocation.objects.filter(stock__product_variant_id=variant.pk).count()
        == allocations_before + preorder_allocations_before
    )
    assert (
        stock.quantity_allocated
        == stock.allocations.aggregate(Sum("quantity_allocated"))[
            "quantity_allocated__sum"
        ]
    )
