from decimal import Decimal

from django.utils import timezone
from freezegun import freeze_time

from ... import DiscountType, DiscountValueType
from ...utils import create_or_update_discount_objects_from_sale_for_checkout
from . import generate_discount_info


def test_create_or_update_discount_objects_from_sale_for_checkout_without_sale(
    checkout_lines_info, checkout_info
):
    # given

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, []
    )

    # then
    for checkout_line_info in checkout_lines_info:
        assert not checkout_line_info.discounts


@freeze_time("2020-12-12 12:00:00")
def test_create_fixed_sale(checkout_lines_info, checkout_info, new_sale):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    sale = new_sale
    sale.products.add(product_line1)
    discount_info_for_new_sale = generate_discount_info(
        sale, products_pks={product_line1.pk}
    )

    sale_channel_listing = sale.channel_listings.get()
    expected_discount_amount = sale_channel_listing.discount_value

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [discount_info_for_new_sale]
    )

    # then
    assert len(line_info1.discounts) == 1
    now = timezone.now()
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.created_at == discount_from_db.created_at == now
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.FIXED
    )
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.name == discount_from_db.name == sale.name
    assert (
        discount_from_info.translated_name == discount_from_db.translated_name is None
    )
    assert discount_from_info.reason == discount_from_db.reason is None
    assert discount_from_info.sale == discount_from_db.sale == sale
    assert discount_from_info.voucher == discount_from_db.voucher is None

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


@freeze_time("2020-12-12 12:00:00")
def test_create_fixed_sale_multiple_quantity_in_lines(
    checkout_lines_with_multiple_quantity_info,
    checkout_info,
    new_sale,
):
    # given
    line_info1 = checkout_lines_with_multiple_quantity_info[0]
    product_line1 = line_info1.product

    sale = new_sale
    sale.products.add(product_line1)
    discount_info_for_new_sale = generate_discount_info(
        sale, products_pks={product_line1.pk}
    )

    sale_channel_listing = sale.channel_listings.get()
    expected_discount_amount = (
        sale_channel_listing.discount_value * line_info1.line.quantity
    )

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info,
        checkout_lines_with_multiple_quantity_info,
        [discount_info_for_new_sale],
    )

    # then
    assert len(line_info1.discounts) == 1
    now = timezone.now()
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.created_at == discount_from_db.created_at == now
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.FIXED
    )
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.name == discount_from_db.name == sale.name
    assert (
        discount_from_info.translated_name == discount_from_db.translated_name is None
    )
    assert discount_from_info.reason == discount_from_db.reason is None
    assert discount_from_info.sale == discount_from_db.sale == sale
    assert discount_from_info.voucher == discount_from_db.voucher is None

    for checkout_line_info in checkout_lines_with_multiple_quantity_info[1:]:
        assert not checkout_line_info.discounts


def test_create_fixed_sale_multiple_quantity_in_lines_more_then_total(
    checkout_lines_with_multiple_quantity_info,
    checkout_info,
    new_sale,
):
    # given
    discount_value = Decimal(15)
    line_info1 = checkout_lines_with_multiple_quantity_info[0]
    product_line1 = line_info1.product

    sale = new_sale
    sale.products.add(product_line1)
    sale_channel_listing = sale.channel_listings.get()
    sale_channel_listing.discount_value = discount_value
    sale_channel_listing.save()
    discount_info_for_new_sale = generate_discount_info(
        sale, products_pks={product_line1.pk}
    )

    expected_discount_amount = (
        sale_channel_listing.discount_value * line_info1.line.quantity
    )
    base_unit_price = line_info1.variant.get_base_price(
        line_info1.channel_listing, line_info1.line.price_override
    )
    expected_discount_amount = (base_unit_price * line_info1.line.quantity).amount

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info,
        checkout_lines_with_multiple_quantity_info,
        [discount_info_for_new_sale],
    )

    # then
    assert discount_value > base_unit_price.amount
    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.FIXED
    )
    assert discount_from_info.value == discount_from_db.value == discount_value
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"

    for checkout_line_info in checkout_lines_with_multiple_quantity_info[1:]:
        assert not checkout_line_info.discounts


@freeze_time("2020-12-12 12:00:00")
def test_create_percentage_sale(
    checkout_lines_info, checkout_info, new_sale_percentage
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    sale = new_sale_percentage
    sale.products.add(product_line1)
    discount_info_for_new_sale_percentage = generate_discount_info(
        sale, products_pks={product_line1.pk}
    )

    sale_channel_listing = sale.channel_listings.get()
    variant_channel_listing = line_info1.variant.channel_listings.get()
    expected_discount_amount = variant_channel_listing.price_amount * (
        sale_channel_listing.discount_value / 100
    )

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [discount_info_for_new_sale_percentage]
    )

    # then
    assert len(line_info1.discounts) == 1
    now = timezone.now()
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.created_at == discount_from_db.created_at == now
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.PERCENTAGE
    )
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.name == discount_from_db.name == sale.name
    assert (
        discount_from_info.translated_name == discount_from_db.translated_name is None
    )
    assert discount_from_info.reason == discount_from_db.reason is None
    assert discount_from_info.sale == discount_from_db.sale == sale
    assert discount_from_info.voucher == discount_from_db.voucher is None

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


@freeze_time("2020-12-12 12:00:00")
def test_create_percentage_sale_multiple_quantity_in_lines(
    checkout_lines_with_multiple_quantity_info,
    checkout_info,
    new_sale_percentage,
):
    # given
    line_info1 = checkout_lines_with_multiple_quantity_info[0]
    product_line1 = line_info1.product

    sale = new_sale_percentage
    sale.products.add(product_line1)
    discount_info_for_new_sale_percentage = generate_discount_info(
        sale, products_pks={product_line1.pk}
    )

    sale_channel_listing = sale.channel_listings.get()
    variant_channel_listing = line_info1.variant.channel_listings.get()
    expected_discount_amount = (
        variant_channel_listing.price_amount
        * line_info1.line.quantity
        * (sale_channel_listing.discount_value / 100)
    )

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info,
        checkout_lines_with_multiple_quantity_info,
        [discount_info_for_new_sale_percentage],
    )

    # then
    assert len(line_info1.discounts) == 1
    now = timezone.now()
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert line_info1.line.quantity > 1
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.created_at == discount_from_db.created_at == now
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.PERCENTAGE
    )
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.name == discount_from_db.name == sale.name
    assert (
        discount_from_info.translated_name == discount_from_db.translated_name is None
    )
    assert discount_from_info.reason == discount_from_db.reason is None
    assert discount_from_info.sale == discount_from_db.sale == sale
    assert discount_from_info.voucher == discount_from_db.voucher is None

    for checkout_line_info in checkout_lines_with_multiple_quantity_info[1:]:
        assert not checkout_line_info.discounts


def test_create_sale_with_translation(
    checkout_lines_info,
    checkout_info,
    new_sale_translation_fr,
):
    # given
    checkout_info.checkout.language_code = "fr"
    checkout_info.checkout.save()

    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    sale = new_sale_translation_fr.sale
    sale.products.add(product_line1)
    discount_info_for_new_sale = generate_discount_info(
        sale, products_pks={product_line1.pk}
    )

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [discount_info_for_new_sale]
    )

    # then
    assert checkout_info.checkout.language_code == "fr"

    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert discount_from_info.name == discount_from_db.name == sale.name
    assert (
        discount_from_info.translated_name
        == discount_from_db.translated_name
        == new_sale_translation_fr.name
    )
    assert discount_from_info.sale == discount_from_db.sale == sale

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_create_fixed_sale_more_then_total(
    checkout_lines_info, checkout_info, new_sale
):
    # given
    discount_value = Decimal(100)

    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    sale = new_sale
    sale.products.add(product_line1)
    sale_channel_listing = sale.channel_listings.get()
    sale_channel_listing.discount_value = discount_value
    sale_channel_listing.save()

    discount_info_for_new_sale = generate_discount_info(
        sale,
        products_pks={product_line1.pk},
        channel_listings={sale_channel_listing.channel.slug: sale_channel_listing},
    )

    base_unit_price = line_info1.variant.get_base_price(
        line_info1.channel_listing, line_info1.line.price_override
    )
    expected_discount_amount = (base_unit_price * line_info1.line.quantity).amount

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [discount_info_for_new_sale]
    )

    # then
    assert discount_value > expected_discount_amount
    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.FIXED
    )
    assert discount_from_info.value == discount_from_db.value == discount_value
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_create_sale_by_product(checkout_lines_info, checkout_info, new_sale):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    sale = new_sale
    sale.products.add(product_line1)
    discount_info_for_new_sale = generate_discount_info(
        sale, products_pks={product_line1.pk}
    )

    sale_channel_listing = sale.channel_listings.get()
    expected_discount_amount = sale_channel_listing.discount_value

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [discount_info_for_new_sale]
    )

    # then
    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.sale == discount_from_db.sale == sale

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_create_sale_by_variant(checkout_lines_info, checkout_info, new_sale):
    # given
    line_info1 = checkout_lines_info[0]
    variant_line1 = line_info1.variant

    sale = new_sale
    sale.variants.add(variant_line1)
    discount_info_for_new_sale = generate_discount_info(
        sale, variant_pks={variant_line1.pk}
    )

    sale_channel_listing = sale.channel_listings.get()
    expected_discount_amount = sale_channel_listing.discount_value

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [discount_info_for_new_sale]
    )

    # then
    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.sale == discount_from_db.sale == sale

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_create_sale_by_collection(checkout_lines_info, checkout_info, new_sale):
    # given
    line_info1 = checkout_lines_info[0]
    collection_line1 = line_info1.collections[1]

    sale = new_sale
    sale.collections.add(collection_line1)
    discount_info_for_new_sale = generate_discount_info(
        sale, collection_pks={collection_line1.pk}
    )

    sale_channel_listing = sale.channel_listings.get()
    expected_discount_amount = sale_channel_listing.discount_value

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [discount_info_for_new_sale]
    )

    # then
    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.sale == discount_from_db.sale == sale

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_create_sale_by_category(checkout_lines_info, checkout_info, new_sale):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product
    category_line1 = product_line1.category

    sale = new_sale
    sale.categories.add(category_line1)
    discount_info_for_new_sale = generate_discount_info(
        sale, category_ids={category_line1.pk}
    )

    sale_channel_listing = sale.channel_listings.get()
    expected_discount_amount = sale_channel_listing.discount_value

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [discount_info_for_new_sale]
    )

    # then
    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.sale == discount_from_db.sale == sale

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_create_sale_two_percentage_sales(
    checkout_lines_info,
    checkout_info,
    new_sale_percentage,
    sale_5_percentage,
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    not_applied_sale = sale_5_percentage
    applied_sale = new_sale_percentage

    sales = [not_applied_sale, applied_sale]
    discount_infos = []
    for sale in sales:
        sale.products.add(product_line1)
        discount_infos.append(
            generate_discount_info(sale, products_pks={product_line1.pk})
        )

    sale_channel_listing = applied_sale.channel_listings.get()
    variant_channel_listing = line_info1.variant.channel_listings.get()
    expected_discount_amount = variant_channel_listing.price_amount * (
        sale_channel_listing.discount_value / 100
    )

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info,
        checkout_lines_info,
        discount_infos,
    )

    # then
    assert (
        not_applied_sale.channel_listings.get().discount_value
        < sale_channel_listing.discount_value
    )

    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()

    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.PERCENTAGE
    )
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.sale == discount_from_db.sale == applied_sale

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_create_sale_two_fixed_sales(
    checkout_lines_info, checkout_info, new_sale, sale_1_usd
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    not_applied_sale = sale_1_usd
    applied_sale = new_sale

    sales = [not_applied_sale, applied_sale]
    discount_infos = []
    for sale in sales:
        sale.products.add(product_line1)
        discount_infos.append(
            generate_discount_info(sale, products_pks={product_line1.pk})
        )

    sale_channel_listing = applied_sale.channel_listings.get()
    expected_discount_amount = sale_channel_listing.discount_value

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info,
        checkout_lines_info,
        discount_infos,
    )

    # then
    assert (
        not_applied_sale.channel_listings.get().discount_value
        < sale_channel_listing.discount_value
    )

    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.FIXED
    )
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.sale == discount_from_db.sale == applied_sale
    assert discount_from_info.voucher == discount_from_db.voucher is None

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_create_sale_fixed_sales_more_then_percentage(
    checkout_lines_info, checkout_info, new_sale, sale_5_percentage
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    not_applied_sale = sale_5_percentage
    applied_sale = new_sale

    sales = [not_applied_sale, applied_sale]
    discount_infos = []
    for sale in sales:
        sale.products.add(product_line1)
        discount_infos.append(
            generate_discount_info(sale, products_pks={product_line1.pk})
        )

    sale_channel_listing = applied_sale.channel_listings.get()
    expected_discount_amount = sale_channel_listing.discount_value

    sale_channel_listing = not_applied_sale.channel_listings.get()
    variant_channel_listing = line_info1.variant.channel_listings.get()
    discount_amount_for_percentage_sale = variant_channel_listing.price_amount * (
        sale_channel_listing.discount_value / 100
    )

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info,
        checkout_lines_info,
        discount_infos,
    )

    # then
    assert discount_amount_for_percentage_sale < sale_channel_listing.discount_value

    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.FIXED
    )
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.sale == discount_from_db.sale == applied_sale
    assert discount_from_info.voucher == discount_from_db.voucher is None

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_create_sale_percentage_sales_more_then_fixed(
    checkout_lines_info,
    checkout_info,
    new_sale_percentage,
    sale_1_usd,
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    not_applied_sale = sale_1_usd
    applied_sale = new_sale_percentage

    sales = [not_applied_sale, applied_sale]
    discount_infos = []
    for sale in sales:
        sale.products.add(product_line1)
        discount_infos.append(
            generate_discount_info(sale, products_pks={product_line1.pk})
        )

    sale_channel_listing = applied_sale.channel_listings.get()
    variant_channel_listing = line_info1.variant.channel_listings.get()
    expected_discount_amount = variant_channel_listing.price_amount * (
        sale_channel_listing.discount_value / 100
    )

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info,
        checkout_lines_info,
        discount_infos,
    )

    # then
    assert (
        not_applied_sale.channel_listings.get().discount_value
        < expected_discount_amount
    )

    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()

    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.PERCENTAGE
    )
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.sale == discount_from_db.sale == applied_sale

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_two_sales_applied_to_two_different_lines(
    checkout_lines_info,
    checkout_info,
    new_sale_percentage,
    sale_1_usd,
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    sale1 = sale_1_usd
    sale1.products.add(product_line1)
    discount_info1 = generate_discount_info(sale1, products_pks={product_line1.pk})

    sale_channel_listing1 = sale1.channel_listings.get()
    expected_discount_amount1 = sale_channel_listing1.discount_value

    line_info2 = checkout_lines_info[1]
    product_line2 = line_info2.product

    sale2 = new_sale_percentage
    sale2.products.add(product_line2)
    discount_info2 = generate_discount_info(sale2, products_pks={product_line2.pk})

    sale_channel_listing2 = sale2.channel_listings.get()
    variant_channel_listing2 = line_info1.variant.channel_listings.get()
    expected_discount_amount2 = variant_channel_listing2.price_amount * (
        sale_channel_listing2.discount_value / 100
    )

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info,
        checkout_lines_info,
        [discount_info1, discount_info2],
    )

    # then
    assert line_info1.product != line_info2.product
    # Checkout discount for first line with fixed sale
    assert len(line_info1.discounts) == 1
    discount_from_info1 = line_info1.discounts[0]
    discount_from_db1 = line_info1.line.discounts.get()

    assert discount_from_info1.line == discount_from_db1.line == line_info1.line
    assert discount_from_info1.type == discount_from_db1.type == DiscountType.SALE
    assert (
        discount_from_info1.value_type
        == discount_from_db1.value_type
        == DiscountValueType.FIXED
    )
    assert (
        discount_from_info1.value
        == discount_from_db1.value
        == sale_channel_listing1.discount_value
    )
    assert (
        discount_from_info1.amount_value
        == discount_from_db1.amount_value
        == expected_discount_amount1
    )
    assert discount_from_info1.currency == discount_from_db1.currency == "USD"
    assert discount_from_info1.sale == discount_from_db1.sale == sale1

    # Checkout discount for second line with percentage sale
    assert len(line_info2.discounts) == 1
    discount_from_info2 = line_info2.discounts[0]
    discount_from_db2 = line_info2.line.discounts.get()

    assert discount_from_info2.line == discount_from_db2.line == line_info2.line
    assert discount_from_info2.type == discount_from_db2.type == DiscountType.SALE
    assert (
        discount_from_info2.value_type
        == discount_from_db2.value_type
        == DiscountValueType.PERCENTAGE
    )
    assert (
        discount_from_info2.value
        == discount_from_db2.value
        == sale_channel_listing2.discount_value
    )
    assert (
        discount_from_info2.amount_value
        == discount_from_db2.amount_value
        == expected_discount_amount2
    )
    assert discount_from_info2.currency == discount_from_db2.currency == "USD"
    assert discount_from_info2.sale == discount_from_db2.sale == sale2

    for checkout_line_info in checkout_lines_info[2:]:
        assert not checkout_line_info.discounts


def test_update_sale_from_fixed_to_percentage(
    checkout_lines_info,
    checkout_info,
    sale_1_usd,
):
    # given
    expected_discount_value = Decimal(50)

    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    sale = sale_1_usd
    sale.products.add(product_line1)
    discount_info = generate_discount_info(sale, products_pks={product_line1.pk})

    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [discount_info]
    )

    sale.type = DiscountValueType.PERCENTAGE
    sale.save()
    sale_channel_listing = sale.channel_listings.get()
    sale_channel_listing.discount_value = expected_discount_value
    sale_channel_listing.save()
    updated_discount_info = generate_discount_info(
        sale,
        products_pks={product_line1.pk},
        channel_listings={sale_channel_listing.channel.slug: sale_channel_listing},
    )

    variant_channel_listing = line_info1.variant.channel_listings.get()
    expected_discount_amount = variant_channel_listing.price_amount * (
        expected_discount_value / 100
    )

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [updated_discount_info]
    )

    # then
    assert len(line_info1.discounts) == 1

    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.PERCENTAGE
    )
    assert discount_from_info.value == discount_from_db.value == expected_discount_value
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.name == discount_from_db.name == sale.name
    assert discount_from_info.sale == discount_from_db.sale == sale

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_update_sale_from_percentage_to_fixed(
    checkout_lines_info,
    checkout_info,
    sale_5_percentage,
):
    # given
    expected_discount_value = Decimal(7)
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    sale = sale_5_percentage
    sale.products.add(product_line1)
    discount_info = generate_discount_info(sale, products_pks={product_line1.pk})

    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [discount_info]
    )

    sale.type = DiscountValueType.FIXED
    sale.save()
    sale_channel_listing = sale.channel_listings.get()
    sale_channel_listing.discount_value = expected_discount_value
    sale_channel_listing.save()
    updated_discount_info = generate_discount_info(
        sale,
        products_pks={product_line1.pk},
        channel_listings={sale_channel_listing.channel.slug: sale_channel_listing},
    )

    expected_discount_amount = expected_discount_value

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [updated_discount_info]
    )

    # then
    assert len(line_info1.discounts) == 1

    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.FIXED
    )
    assert discount_from_info.value == discount_from_db.value == expected_discount_value
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.name == discount_from_db.name == sale.name
    assert discount_from_info.sale == discount_from_db.sale == sale

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_replace_sale_from_fixed_to_percentage(
    checkout_lines_info,
    checkout_info,
    sale_1_usd,
    sale_5_percentage,
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    start_sale = sale_1_usd
    start_sale.products.add(product_line1)
    discount_info = generate_discount_info(start_sale, products_pks={product_line1.pk})

    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [discount_info]
    )

    target_sale = sale_5_percentage
    target_sale.products.add(product_line1)
    sale_channel_listing = target_sale.channel_listings.get()

    updated_discount_info = generate_discount_info(
        target_sale, products_pks={product_line1.pk}
    )

    variant_channel_listing = line_info1.variant.channel_listings.get()
    expected_discount_amount = variant_channel_listing.price_amount * (
        sale_channel_listing.discount_value / 100
    )

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [updated_discount_info]
    )

    # then
    assert len(line_info1.discounts) == 1

    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.PERCENTAGE
    )
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.name == discount_from_db.name == target_sale.name
    assert discount_from_info.sale == discount_from_db.sale == target_sale

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_replace_sale_from_percentage_to_fixed(
    checkout_lines_info,
    checkout_info,
    sale_1_usd,
    sale_5_percentage,
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    start_sale = sale_5_percentage
    start_sale.products.add(product_line1)
    discount_info = generate_discount_info(start_sale, products_pks={product_line1.pk})

    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [discount_info]
    )

    target_sale = sale_1_usd
    target_sale.products.add(product_line1)
    sale_channel_listing = target_sale.channel_listings.get()

    updated_discount_info = generate_discount_info(
        target_sale,
        products_pks={product_line1.pk},
    )

    expected_discount_amount = sale_channel_listing.discount_value

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, checkout_lines_info, [updated_discount_info]
    )

    # then
    assert len(line_info1.discounts) == 1

    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.SALE
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == DiscountValueType.FIXED
    )
    assert (
        discount_from_info.value
        == discount_from_db.value
        == sale_channel_listing.discount_value
    )
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.name == discount_from_db.name == target_sale.name
    assert discount_from_info.sale == discount_from_db.sale == target_sale

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts
