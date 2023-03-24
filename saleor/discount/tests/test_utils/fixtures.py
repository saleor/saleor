import pytest

from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....plugins.manager import get_plugins_manager
from ... import DiscountInfo, DiscountValueType
from ...models import Sale, SaleChannelListing
from ...utils import fetch_sale_channel_listings


@pytest.fixture
def checkout_lines_info(checkout_with_items, categories, published_collections):
    lines = checkout_with_items.lines.all()
    category1, category2 = categories

    product1 = lines[0].variant.product
    product1.category = category1
    product1.collections.add(*published_collections[:2])
    product1.save()

    product2 = lines[1].variant.product
    product2.category = category2
    product2.collections.add(published_collections[0])
    product2.save()

    lines_info, _ = fetch_checkout_lines(checkout_with_items)
    return lines_info


@pytest.fixture
def checkout_info(checkout_lines_info):
    manager = get_plugins_manager()
    checkout = checkout_lines_info[0].line.checkout
    checkout_info = fetch_checkout_info(checkout, checkout_lines_info, manager)
    return checkout_info


@pytest.fixture
def checkout_lines_with_multiple_quantity_info(
    checkout_with_items, categories, published_collections
):
    checkout_with_items.lines.update(quantity=5)
    lines = checkout_with_items.lines.all()
    category1, category2 = categories

    product1 = lines[0].variant.product
    product1.category = category1
    product1.collections.add(*published_collections[:2])
    product1.save()

    product2 = lines[1].variant.product
    product2.category = category2
    product2.collections.add(published_collections[0])
    product2.save()

    lines_info, _ = fetch_checkout_lines(checkout_with_items)
    return lines_info


@pytest.fixture
def discount_info_for_new_sale(new_sale):
    channel_listings = fetch_sale_channel_listings([new_sale.pk])[new_sale.pk]

    return DiscountInfo(
        sale=new_sale,
        category_ids=set(),
        channel_listings=channel_listings,
        collection_ids=set(),
        product_ids=set(),
        variants_ids=set(),
    )


@pytest.fixture
def new_sale_percentage(channel_USD):
    sale = Sale.objects.create(name="Sale 25%", type=DiscountValueType.PERCENTAGE)
    SaleChannelListing.objects.create(
        sale=sale,
        channel=channel_USD,
        discount_value=25,
        currency=channel_USD.currency_code,
    )
    return sale


@pytest.fixture
def sale_5_percentage(channel_USD):
    sale = Sale.objects.create(name="Sale 5%", type=DiscountValueType.PERCENTAGE)
    SaleChannelListing.objects.create(
        sale=sale,
        channel=channel_USD,
        discount_value=5,
        currency=channel_USD.currency_code,
    )
    return sale


@pytest.fixture
def sale_1_usd(channel_USD):
    sale = Sale.objects.create(name="Sale 1 USD", type=DiscountValueType.FIXED)
    SaleChannelListing.objects.create(
        sale=sale,
        channel=channel_USD,
        discount_value=1,
        currency=channel_USD.currency_code,
    )
    return sale
