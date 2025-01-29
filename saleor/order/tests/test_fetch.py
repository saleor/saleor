from decimal import Decimal

import pytest

from ..fetch import EditableOrderLineInfo, fetch_draft_order_lines_info


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_fetch_draft_order_lines_info(
    draft_order_and_promotions, django_assert_num_queries, count_queries
):
    # given
    order, rule_catalogue, rule_total, rule_gift = draft_order_and_promotions
    channel = order.channel
    lines = order.lines.all()
    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]
    catalogue_discount = line_2.discounts.get()

    manual_discount = line_1.discounts.create(
        value=Decimal(1),
        amount_value=Decimal(1),
        currency=channel.currency_code,
        name="Manual line discount",
    )
    rule_translation = "Rule translation"
    rule_catalogue.translations.create(
        language_code=order.language_code, name=rule_translation
    )
    promotion_translation = "Promotion"
    rule_catalogue.promotion.translations.create(
        language_code=order.language_code, name=promotion_translation
    )

    # when
    with django_assert_num_queries(8):
        lines_info = fetch_draft_order_lines_info(order)

    # then
    line_info_1 = [line_info for line_info in lines_info if line_info.line == line_1][0]
    line_info_2 = [line_info for line_info in lines_info if line_info.line == line_2][0]

    variant_1 = line_1.variant
    assert line_info_1.variant == variant_1
    assert line_info_1.discounts == [manual_discount]
    assert line_info_1.channel == channel
    assert line_info_1.voucher is None

    variant_2 = line_2.variant
    assert line_info_2.variant == variant_2
    assert line_info_2.discounts == [catalogue_discount]
    assert line_info_2.channel == channel
    assert line_info_2.voucher is None


def test_editable_order_line_info_variant_discounted_price(
    order_with_lines_and_catalogue_promotion,
):
    # given
    order_line = order_with_lines_and_catalogue_promotion.lines.get(quantity=3)
    order = order_with_lines_and_catalogue_promotion
    channel = order.channel
    variant = order_line.variant
    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    product = variant.product
    product_type = product.product_type
    discounts = order_line.discounts.all()

    expected_discounted_variant_price = variant_channel_listing.discounted_price
    assert variant_channel_listing.discounted_price != variant_channel_listing.price

    # when
    order_line_info = EditableOrderLineInfo(
        line=order_line,
        variant=variant,
        product=product,
        product_type=product_type,
        collections=[],
        discounts=discounts,
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert order_line_info.variant_discounted_price == expected_discounted_variant_price
