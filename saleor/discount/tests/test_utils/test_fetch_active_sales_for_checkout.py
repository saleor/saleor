from unittest import mock

from ....checkout.fetch import fetch_checkout_lines
from ....discount.models import Sale, SaleChannelListing
from ... import DiscountInfo
from ...utils import fetch_active_sales_for_checkout, fetch_sale_channel_listings


def test_fetch_sale_channel_listings(new_sale, sale_with_many_channels):
    # given
    sales = [new_sale, sale_with_many_channels]

    expected_channel_listings_map = {}
    for sale in sales:
        expected_channel_listings_map[sale.pk] = {
            channel_listing.channel.slug: channel_listing
            for channel_listing in sale.channel_listings.all()
        }

    # when
    channel_listings_map = fetch_sale_channel_listings(sales)

    # then
    assert channel_listings_map == expected_channel_listings_map


def test_fetch_active_sale_for_no_sale_to_apply(checkout_lines_info, new_sale):
    # given

    # when
    sales = fetch_active_sales_for_checkout(checkout_lines_info)

    # then
    assert sales == []


@mock.patch("saleor.discount.utils.fetch_products")
@mock.patch("saleor.discount.utils.fetch_variants")
@mock.patch("saleor.discount.utils.fetch_categories")
@mock.patch("saleor.discount.utils.fetch_collections")
@mock.patch("saleor.discount.utils.fetch_sale_channel_listings")
def test_fetch_active_sale_for_empty_checkout(
    mocked_fetch_sale_channel_listings,
    mocked_fetch_collections,
    mocked_fetch_categories,
    mocked_fetch_variants,
    mocked_fetch_products,
    checkout,
):
    # given
    lines_info, _ = fetch_checkout_lines(checkout)

    # when
    sales = fetch_active_sales_for_checkout(lines_info)

    # then
    assert sales == []
    mocked_fetch_sale_channel_listings.assert_not_called()
    mocked_fetch_collections.assert_not_called()
    mocked_fetch_categories.assert_not_called()
    mocked_fetch_variants.assert_not_called()
    mocked_fetch_products.assert_not_called()


def test_fetch_active_sale_for_products(
    checkout_lines_info, new_sale, product_with_two_variants
):
    # given
    line_info1, line_info2 = checkout_lines_info[:2]
    new_sale.products.add(
        # We add a not-used product to the sale to check that
        # `fetch_active_sales_for_checkout` don't over-fetch data.
        *[line_info1.product, line_info2.product, product_with_two_variants]
    )
    channel_listings = fetch_sale_channel_listings([new_sale.pk])[new_sale.pk]

    discount_info = DiscountInfo(
        sale=new_sale,
        category_ids=set(),
        channel_listings=channel_listings,
        collection_ids=set(),
        product_ids={line_info1.product.pk, line_info2.product.pk},
        variants_ids=set(),
    )

    # when
    sales = fetch_active_sales_for_checkout(checkout_lines_info)

    # then
    assert sales == [discount_info]


def test_fetch_active_sale_for_variants(
    checkout_lines_info, new_sale, product_with_two_variants
):
    # given
    line_info1, line_info2 = checkout_lines_info[:2]
    # We add a not-used product variants to the sale to check that
    # `fetch_active_sales_for_checkout` don't over-fetch data.
    variants = list(product_with_two_variants.variants.all())
    variants.extend([line_info1.variant, line_info2.variant])
    new_sale.variants.add(*variants)
    channel_listings = fetch_sale_channel_listings([new_sale.pk])[new_sale.pk]

    discount_info = DiscountInfo(
        sale=new_sale,
        category_ids=set(),
        channel_listings=channel_listings,
        collection_ids=set(),
        product_ids=set(),
        variants_ids={line_info1.variant.pk, line_info2.variant.pk},
    )

    # when
    sales = fetch_active_sales_for_checkout(checkout_lines_info)

    # then
    assert sales == [discount_info]


def test_fetch_active_sale_for_categories(
    checkout_lines_info, new_sale, categories, categories_tree
):
    # given
    new_sale.categories.add(*categories)
    # We add a not-used category to the sale to check that
    # `fetch_active_sales_for_checkout` don't over-fetch data.
    new_sale.categories.add(categories_tree)
    channel_listings = fetch_sale_channel_listings([new_sale.pk])[new_sale.pk]

    discount_info = DiscountInfo(
        sale=new_sale,
        category_ids={cat.pk for cat in categories},
        channel_listings=channel_listings,
        collection_ids=set(),
        product_ids=set(),
        variants_ids=set(),
    )

    # when
    sales = fetch_active_sales_for_checkout(checkout_lines_info)

    # then
    assert sales == [discount_info]


def test_fetch_active_sale_for_only_subcategory(
    checkout_lines_info, new_sale, categories_tree
):
    # given
    category = categories_tree
    subcategory = category.children.first()
    new_sale.categories.add(category)
    channel_listings = fetch_sale_channel_listings([new_sale.pk])[new_sale.pk]

    product1 = checkout_lines_info[0].variant.product
    product1.category = subcategory
    product1.save()

    discount_info = DiscountInfo(
        sale=new_sale,
        category_ids={subcategory.pk},
        channel_listings=channel_listings,
        collection_ids=set(),
        product_ids=set(),
        variants_ids=set(),
    )

    # when
    sales = fetch_active_sales_for_checkout(checkout_lines_info)

    # then
    assert sales == [discount_info]


def test_fetch_active_sale_for_subcategory_and_category(
    checkout_lines_info, new_sale, categories_tree
):
    # given
    category = categories_tree
    subcategory = category.children.first()
    new_sale.categories.add(*[category, subcategory])
    channel_listings = fetch_sale_channel_listings([new_sale.pk])[new_sale.pk]

    product1 = checkout_lines_info[0].variant.product
    product1.category = subcategory
    product1.save()
    product2 = checkout_lines_info[1].variant.product
    product2.category = category
    product2.save()

    discount_info = DiscountInfo(
        sale=new_sale,
        category_ids={subcategory.pk, category.pk},
        channel_listings=channel_listings,
        collection_ids=set(),
        product_ids=set(),
        variants_ids=set(),
    )

    # when
    sales = fetch_active_sales_for_checkout(checkout_lines_info)

    # then
    assert sales == [discount_info]


def test_fetch_active_sale_for_collections(
    checkout_lines_info, new_sale, published_collections
):
    # given
    collections_in_sale = published_collections[:2]
    # We add a not-used collections to the sale to check that
    # `fetch_active_sales_for_checkout` don't over-fetch data.
    new_sale.collections.add(*published_collections)
    channel_listings = fetch_sale_channel_listings([new_sale.pk])[new_sale.pk]

    discount_info = DiscountInfo(
        sale=new_sale,
        category_ids=set(),
        channel_listings=channel_listings,
        collection_ids={col.pk for col in collections_in_sale},
        product_ids=set(),
        variants_ids=set(),
    )

    # when
    sales = fetch_active_sales_for_checkout(checkout_lines_info)

    # then
    assert sales == [discount_info]


def test_fetch_active_sale_for_all_relations(
    checkout_lines_info, new_sale, published_collections, categories
):
    # given
    line_info1, line_info2 = checkout_lines_info[:2]
    collections_in_sale = published_collections[:2]
    channel_listings = fetch_sale_channel_listings([new_sale.pk])[new_sale.pk]

    new_sale.products.add(*[line_info1.product, line_info2.product])
    new_sale.variants.add(*[line_info1.variant, line_info2.variant])
    new_sale.categories.add(*categories)
    new_sale.collections.add(*collections_in_sale)

    discount_info = DiscountInfo(
        sale=new_sale,
        category_ids={cat.pk for cat in categories},
        channel_listings=channel_listings,
        collection_ids={col.pk for col in collections_in_sale},
        product_ids={line_info1.product.pk, line_info2.product.pk},
        variants_ids={line_info1.variant.pk, line_info2.variant.pk},
    )

    # when
    sales = fetch_active_sales_for_checkout(checkout_lines_info)

    # then
    assert sales == [discount_info]


def test_fetch_active_sale_for_many_sales(
    checkout_lines_info, published_collections, categories, channel_USD
):
    # given
    line_info1, line_info2 = checkout_lines_info[:2]
    collections_in_sale = published_collections[:2]

    sales = Sale.objects.bulk_create(
        [
            Sale(name="Sale1"),
            Sale(name="Sale2"),
            Sale(name="Sale3"),
        ]
    )
    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(
                sale=sale,
                channel=channel_USD,
                discount_value=5,
                currency=channel_USD.currency_code,
            )
            for sale in sales
        ]
    )

    channel_listings_by_sale_id_map = fetch_sale_channel_listings(
        [sale.pk for sale in sales]
    )

    sales[0].products.add(*[line_info1.product, line_info2.product])
    discount_info1 = DiscountInfo(
        sale=sales[0],
        category_ids=set(),
        channel_listings=channel_listings_by_sale_id_map[sales[0].pk],
        collection_ids=set(),
        product_ids={line_info1.product.pk, line_info2.product.pk},
        variants_ids=set(),
    )

    sales[1].variants.add(*[line_info1.variant, line_info2.variant])
    discount_info2 = DiscountInfo(
        sale=sales[1],
        category_ids=set(),
        channel_listings=channel_listings_by_sale_id_map[sales[1].pk],
        collection_ids=set(),
        product_ids=set(),
        variants_ids={line_info1.variant.pk, line_info2.variant.pk},
    )

    sales[2].categories.add(*categories)
    sales[2].collections.add(*collections_in_sale)
    discount_info3 = DiscountInfo(
        sale=sales[2],
        category_ids={cat.pk for cat in categories},
        channel_listings=channel_listings_by_sale_id_map[sales[2].pk],
        collection_ids={col.pk for col in collections_in_sale},
        product_ids=set(),
        variants_ids=set(),
    )

    # when
    sales = fetch_active_sales_for_checkout(checkout_lines_info)

    # then
    assert sales == [discount_info1, discount_info2, discount_info3]
