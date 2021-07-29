from ...product.models import ProductVariantChannelListing
from ..management import complete_preorder
from ..models import Allocation, PreorderAllocation


def test_complete_preorder(
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

    allocations_before = Allocation.objects.filter(
        stock__product_variant_id=variant.pk
    ).count()

    complete_preorder(variant)

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

    assert variant.is_preorder is False
    assert variant.preorder_global_threshold is None
    assert variant.preorder_end_date is None

    channel_listings = ProductVariantChannelListing.objects.filter(
        variant_id=variant.pk
    )
    for channel_listing in channel_listings:
        assert channel_listing.preorder_quantity_threshold is None


def test_complete_preorder_order_without_shipping_method(
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
):
    """When order has no shiping method set,
    use warehouse based on country from address."""
    variant = preorder_variant_global_and_channel_threshold
    order = preorder_allocation.order_line.order
    assert order.shipping_method is None

    channel_listings_id = ProductVariantChannelListing.objects.filter(
        variant_id=variant.pk
    ).values_list("id", flat=True)
    preorder_allocations_before = PreorderAllocation.objects.filter(
        product_variant_channel_listing_id__in=channel_listings_id
    ).count()

    allocations_before = Allocation.objects.filter(
        stock__product_variant_id=variant.pk
    ).count()

    complete_preorder(variant)

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
