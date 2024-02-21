from decimal import Decimal

from ...product.models import ProductVariantChannelListing
from ..fetch import fetch_draft_order_lines_info


def test_fetch_draft_order_lines_info(draft_order_and_promotions):
    # given
    order, rule_catalogue, rule_total, rule_gift = draft_order_and_promotions
    channel = order.channel
    lines = order.lines.all()
    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]

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
    lines_info = fetch_draft_order_lines_info(order)

    # then
    line_info_1 = [line_info for line_info in lines_info if line_info.line == line_1][0]
    line_info_2 = [line_info for line_info in lines_info if line_info.line == line_2][0]

    variant_1 = line_1.variant
    assert line_info_1.variant == variant_1
    assert (
        line_info_1.channel_listing
        == ProductVariantChannelListing.objects.filter(
            channel=channel, variant=variant_1
        ).first()
    )
    assert line_info_1.discounts == [manual_discount]
    assert line_info_1.channel == channel
    assert line_info_1.voucher is None
    assert line_info_1.rules_info == []
    assert line_info_1.should_refresh_discounts is False

    variant_2 = line_2.variant
    assert line_info_2.variant == variant_2
    assert (
        line_info_2.channel_listing
        == ProductVariantChannelListing.objects.filter(
            channel=channel, variant=variant_2
        ).first()
    )
    assert line_info_2.discounts == []
    assert line_info_2.channel == channel
    assert line_info_2.voucher is None
    rule_info_2 = line_info_2.rules_info[0]
    assert rule_info_2.rule == rule_catalogue
    assert rule_info_2.variant_listing_promotion_rule
    assert rule_info_2.promotion == rule_catalogue.promotion
    assert rule_info_2.promotion_translation.name == promotion_translation
    assert rule_info_2.rule_translation.name == rule_translation
    assert line_info_2.should_refresh_discounts is False
