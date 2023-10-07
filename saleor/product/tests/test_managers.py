from saleor.product.models import ProductVariant


def test_available_quantity_with_no_allocations(variant, allocations):
    stocks = variant.stocks.first()
    stocks.allocations.all().delete()
    assert stocks.quantity == 15

    assert stocks.allocations.count() == 0
    # No allocations have been made, so available_quantity should be equal to quantity
    instance = ProductVariant.objects.annotate_quantities().get(pk=variant.pk)
    assert instance.available_quantity == 15


def test_available_quantity_with_allocations(variant, allocations):
    stocks = variant.stocks.first()

    allocation_quantity = sum(
        allocation.quantity_allocated for allocation in stocks.allocations.all()
    )
    assert stocks.allocations.count() == 3
    assert stocks.quantity == 15
    assert allocation_quantity == 7

    #  Available quantity should be quantity - quantity_allocated
    instance = ProductVariant.objects.annotate_quantities().get(pk=variant.pk)
    assert instance.available_quantity == 15 - 7


def test_available_quantity_with_allocations_quantity_zero(variant, allocations):
    stocks = variant.stocks.first()
    stocks.allocations.update(quantity_allocated=0)

    assert stocks.allocations.count() == 3
    assert stocks.quantity == 15

    # Allocations have been cleared, so available_quantity should be equal to quantity
    instance = ProductVariant.objects.annotate_quantities().get(pk=variant.pk)
    assert instance.available_quantity == 15


def test_available_quantity_with_insufficient_stock(variant, allocations):
    stocks = variant.stocks.first()
    stocks.allocations.update(quantity_allocated=100)

    assert stocks.allocations.count() == 3
    assert stocks.quantity == 15

    # Allocations are greater than available quantity, so available_quantity should
    # be negative.
    instance = ProductVariant.objects.annotate_quantities().get(pk=variant.pk)
    assert instance.available_quantity == 15 - 300


def test_available_quantity_with_no_stock(variant):
    # Delete the stocks to simulate a product variant with no available stock
    variant.stocks.all().delete()

    instance = ProductVariant.objects.annotate_quantities().get(pk=variant.pk)
    assert instance.available_quantity == 0
