import pytest
from django.db.models import Sum
from django.db.models.functions import Coalesce

from ...core.exceptions import InsufficientStock
from ...order import OrderLineData
from ...order.models import OrderLine
from ...warehouse.models import Stock
from ..management import (
    allocate_stocks,
    deallocate_stock,
    deallocate_stock_for_order,
    decrease_stock,
    increase_allocations,
    increase_stock,
)
from ..models import Allocation

COUNTRY_CODE = "US"


def test_allocate_stocks(order_line, stock, channel_USD):
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    line_data = OrderLineData(line=order_line, variant=order_line.variant, quantity=50)

    allocate_stocks([line_data], COUNTRY_CODE, channel_USD.slug)

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 50


def test_allocate_stocks_multiple_lines(order_line, order, product, stock, channel_USD):
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    variant_2 = product.variants.first()
    stock_2 = Stock.objects.get(product_variant=variant_2)

    order_line_2 = OrderLine.objects.get(pk=order_line.pk)
    order_line_2.pk = None
    order_line_2.product_name = product.name
    order_line_2.variant_name = variant_2.name
    order_line_2.product_sku = variant_2.sku
    order_line_2.variant = variant_2
    order_line_2.save()

    quantity_1 = 50
    quantity_2 = 5
    line_data_1 = OrderLineData(
        line=order_line, variant=order_line.variant, quantity=quantity_1
    )
    line_data_2 = OrderLineData(
        line=order_line_2, variant=variant_2, quantity=quantity_2
    )

    allocate_stocks([line_data_1, line_data_2], COUNTRY_CODE, channel_USD.slug)

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == quantity_1

    stock_2.refresh_from_db()
    allocation = Allocation.objects.get(order_line=order_line_2, stock=stock_2)
    assert allocation.quantity_allocated == quantity_2


def test_allocate_stock_many_stocks(order_line, variant_with_many_stocks, channel_USD):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all()

    line_data = OrderLineData(line=order_line, variant=order_line.variant, quantity=5)
    allocate_stocks([line_data], COUNTRY_CODE, channel_USD.slug)

    allocations = Allocation.objects.filter(order_line=order_line, stock__in=stocks)
    assert allocations[0].quantity_allocated == 4
    assert allocations[1].quantity_allocated == 1


def test_allocate_stock_many_stocks_partially_allocated(
    order_line,
    order_line_with_allocation_in_many_stocks,
    order_line_with_one_allocation,
    channel_USD,
):
    allocated_line = order_line_with_allocation_in_many_stocks
    variant = allocated_line.variant
    stocks = variant.stocks.all()

    line_data = OrderLineData(line=order_line, variant=order_line.variant, quantity=3)
    allocate_stocks([line_data], COUNTRY_CODE, channel_USD.slug)

    allocations = Allocation.objects.filter(order_line=order_line, stock__in=stocks)
    assert allocations[0].quantity_allocated == 1
    assert allocations[1].quantity_allocated == 2


def test_allocate_stock_partially_allocated_insufficient_stocks(
    order_line, order_line_with_allocation_in_many_stocks, channel_USD
):
    allocated_line = order_line_with_allocation_in_many_stocks
    variant = allocated_line.variant
    stocks = variant.stocks.all()

    line_data = OrderLineData(line=order_line, variant=order_line.variant, quantity=6)
    with pytest.raises(InsufficientStock):
        allocate_stocks([line_data], COUNTRY_CODE, channel_USD.slug)

    assert not Allocation.objects.filter(
        order_line=order_line, stock__in=stocks
    ).exists()


def test_allocate_stocks_no_channel_shipping_zones(order_line, stock, channel_USD):
    channel_USD.shipping_zones.clear()

    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    line_data = OrderLineData(line=order_line, variant=order_line.variant, quantity=50)
    with pytest.raises(InsufficientStock):
        allocate_stocks([line_data], COUNTRY_CODE, channel_USD.slug)


def test_allocate_stock_insufficient_stocks(
    order_line, variant_with_many_stocks, channel_USD
):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all()

    line_data = OrderLineData(line=order_line, variant=order_line.variant, quantity=10)
    with pytest.raises(InsufficientStock):
        allocate_stocks([line_data], COUNTRY_CODE, channel_USD.slug)

    assert not Allocation.objects.filter(
        order_line=order_line, stock__in=stocks
    ).exists()


def test_allocate_stock_insufficient_stocks_for_multiple_lines(
    order_line, variant_with_many_stocks, product, channel_USD
):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all()

    variant_2 = product.variants.first()

    order_line_2 = OrderLine.objects.get(pk=order_line.pk)
    order_line_2.pk = None
    order_line_2.product_name = product.name
    order_line_2.variant_name = variant_2.name
    order_line_2.product_sku = variant_2.sku
    order_line_2.variant = variant_2
    order_line_2.save()

    quantity_1 = 100
    quantity_2 = 100
    line_data_1 = OrderLineData(
        line=order_line, variant=order_line.variant, quantity=quantity_1
    )
    line_data_2 = OrderLineData(
        line=order_line_2, variant=variant_2, quantity=quantity_2
    )

    with pytest.raises(InsufficientStock) as exc:
        allocate_stocks([line_data_1, line_data_2], COUNTRY_CODE, channel_USD.slug)

    assert set(item.variant for item in exc._excinfo[1].items) == {variant, variant_2}

    assert not Allocation.objects.filter(
        order_line=order_line, stock__in=stocks
    ).exists()


def test_deallocate_stock(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    deallocate_stock(
        [
            OrderLineData(
                line=allocation.order_line, quantity=80, variant=stock.product_variant
            )
        ]
    )

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 0


def test_deallocate_stock_partially(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    deallocate_stock(
        [
            OrderLineData(
                line=allocation.order_line, quantity=50, variant=stock.product_variant
            )
        ]
    )

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 30


def test_deallocate_stock_many_allocations(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks

    deallocate_stock(
        [OrderLineData(line=order_line, quantity=3, variant=order_line.variant)]
    )

    allocations = order_line.allocations.all()
    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 0


def test_deallocate_stock_many_allocations_partially(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks

    deallocate_stock(
        [OrderLineData(line=order_line, quantity=1, variant=order_line.variant)]
    )

    allocations = order_line.allocations.all()
    assert allocations[0].quantity_allocated == 1
    assert allocations[1].quantity_allocated == 1


def test_increase_stock_without_allocate(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    increase_stock(allocation.order_line, stock.warehouse, 50, allocate=False)

    stock.refresh_from_db()
    assert stock.quantity == 150
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 80


def test_increase_stock_with_allocate(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    increase_stock(allocation.order_line, stock.warehouse, 50, allocate=True)

    stock.refresh_from_db()
    assert stock.quantity == 150
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 130


def test_increase_stock_with_new_allocation(order_line, stock):
    assert not Allocation.objects.filter(order_line=order_line, stock=stock).exists()
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    increase_stock(order_line, stock.warehouse, 50, allocate=True)

    stock.refresh_from_db()
    assert stock.quantity == 150
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 50


@pytest.mark.parametrize("quantity", (19, 20))
def test_increase_allocations(quantity, allocation):
    order_line = allocation.order_line
    order_line_info = OrderLineData(
        line=order_line,
        quantity=quantity,
        variant=order_line.variant,
        warehouse_pk=allocation.stock.warehouse.pk,
    )
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    initially_allocated = 80
    allocation.quantity_allocated = initially_allocated
    allocation.save(update_fields=["quantity_allocated"])

    increase_allocations([order_line_info], order_line.order.channel.slug)

    stock.refresh_from_db()
    assert stock.quantity == 100
    assert (
        order_line.allocations.all().aggregate(Sum("quantity_allocated"))[
            "quantity_allocated__sum"
        ]
        == initially_allocated + quantity
    )


def test_increase_allocation_insufficient_stock(allocation):
    order_line = allocation.order_line
    order_line_info = OrderLineData(
        line=order_line,
        quantity=21,
        variant=order_line.variant,
        warehouse_pk=allocation.stock.warehouse.pk,
    )
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    initially_allocated = 80
    allocation.quantity_allocated = initially_allocated
    allocation.save(update_fields=["quantity_allocated"])

    with pytest.raises(InsufficientStock):
        increase_allocations([order_line_info], order_line.order.channel.slug)

    stock.refresh_from_db()
    assert stock.quantity == 100
    assert (
        order_line.allocations.all().aggregate(Sum("quantity_allocated"))[
            "quantity_allocated__sum"
        ]
        == initially_allocated
    )


def test_decrease_stock(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])
    warehouse_pk = allocation.stock.warehouse.pk

    decrease_stock(
        [
            OrderLineData(
                line=allocation.order_line,
                quantity=50,
                variant=stock.product_variant,
                warehouse_pk=warehouse_pk,
            )
        ],
    )

    stock.refresh_from_db()
    assert stock.quantity == 50
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 30


@pytest.mark.parametrize("quantity, expected_allocated", ((50, 30), (200, 0)))
def test_decrease_stock_without_stock_update(quantity, expected_allocated, allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])
    warehouse_pk = allocation.stock.warehouse.pk

    decrease_stock(
        [
            OrderLineData(
                line=allocation.order_line,
                quantity=quantity,
                variant=stock.product_variant,
                warehouse_pk=warehouse_pk,
            )
        ],
        update_stocks=False,
    )

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == expected_allocated


def test_decrease_stock_multiple_lines(allocations):
    allocation_1 = allocations[0]
    allocation_2 = allocations[0]

    stock = allocation_1.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation_1.quantity_allocated = 80
    allocation_1.save(update_fields=["quantity_allocated"])
    warehouse_pk_1 = allocation_1.stock.warehouse.pk

    allocation_2.quantity_allocated = 80
    allocation_2.save(update_fields=["quantity_allocated"])
    warehouse_pk_2 = allocation_2.stock.warehouse.pk

    decrease_stock(
        [
            OrderLineData(
                line=allocation_1.order_line,
                quantity=50,
                variant=allocation_1.order_line.variant,
                warehouse_pk=warehouse_pk_1,
            ),
            OrderLineData(
                line=allocation_2.order_line,
                quantity=20,
                variant=allocation_2.order_line.variant,
                warehouse_pk=warehouse_pk_2,
            ),
        ],
    )

    stock.refresh_from_db()
    assert stock.quantity == 30
    allocation_1.refresh_from_db()
    assert allocation_1.quantity_allocated == 10


def test_decrease_stock_partially(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])
    warehouse_pk = allocation.stock.warehouse.pk

    decrease_stock(
        [
            OrderLineData(
                line=allocation.order_line,
                quantity=80,
                variant=stock.product_variant,
                warehouse_pk=str(warehouse_pk),
            )
        ],
    )

    stock.refresh_from_db()
    assert stock.quantity == 20
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 0


def test_decrease_stock_many_allocations(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks
    allocations = order_line.allocations.all()
    warehouse_pk = allocations[1].stock.warehouse.pk

    decrease_stock(
        [
            OrderLineData(
                line=order_line,
                quantity=3,
                variant=order_line.variant,
                warehouse_pk=str(warehouse_pk),
            )
        ],
    )

    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 0
    assert allocations[0].stock.quantity == 4
    assert allocations[1].stock.quantity == 0


def test_decrease_stock_many_allocations_partially(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks
    allocations = order_line.allocations.all()
    warehouse_pk = allocations[0].stock.warehouse.pk

    decrease_stock(
        [
            OrderLineData(
                line=order_line,
                quantity=2,
                variant=order_line.variant,
                warehouse_pk=str(warehouse_pk),
            )
        ],
    )

    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 1
    assert allocations[0].stock.quantity == 2
    assert allocations[1].stock.quantity == 3


def test_decrease_stock_more_then_allocated(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks
    allocations = order_line.allocations.all()
    warehouse_pk = allocations[0].stock.warehouse.pk
    quantity_allocated = allocations.aggregate(
        quantity_allocated=Coalesce(Sum("quantity_allocated"), 0)
    )["quantity_allocated"]
    assert quantity_allocated < 4

    decrease_stock(
        [
            OrderLineData(
                line=order_line,
                quantity=4,
                variant=order_line.variant,
                warehouse_pk=warehouse_pk,
            )
        ],
    )

    allocations = order_line.allocations.all()
    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 0
    assert allocations[0].stock.quantity == 0
    assert allocations[1].stock.quantity == 3


def test_decrease_stock_insufficient_stock(allocation):
    stock = allocation.stock
    stock.quantity = 20
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])
    warehouse_pk = allocation.stock.warehouse.pk

    with pytest.raises(InsufficientStock):
        decrease_stock(
            [
                OrderLineData(
                    line=allocation.order_line,
                    quantity=50,
                    variant=stock.product_variant,
                    warehouse_pk=warehouse_pk,
                )
            ],
        )

    stock.refresh_from_db()
    assert stock.quantity == 20
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 80


def test_deallocate_stock_for_order(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks
    order = order_line.order

    deallocate_stock_for_order(order)

    allocations = order_line.allocations.all()
    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 0
