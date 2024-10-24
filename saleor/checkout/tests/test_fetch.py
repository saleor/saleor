from ..fetch import CheckoutLineInfo


def test_checkout_line_info_undiscounted_unit_price(checkout_with_item_on_promotion):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()

    expected_variant_price = variant_channel_listing.price

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=variant_channel_listing,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert checkout_line_info.undiscounted_unit_price == expected_variant_price


def test_checkout_line_info_undiscounted_unit_price_without_listing(
    checkout_with_item_on_promotion,
):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()

    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    expected_variant_price = variant_channel_listing.price

    variant.channel_listings.all().delete()

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=None,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert checkout_line_info.undiscounted_unit_price == expected_variant_price


def test_checkout_line_info_undiscounted_unit_price_when_listing_without_price(
    checkout_with_item_on_promotion,
):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()

    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    expected_variant_price = variant_channel_listing.price

    variant_channel_listing.price_amount = None
    variant_channel_listing.save(update_fields=["price_amount"])

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=None,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert checkout_line_info.undiscounted_unit_price == expected_variant_price


def test_checkout_line_info_variant_discounted_price(checkout_with_item_on_promotion):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()

    expected_discounted_variant_price = variant_channel_listing.discounted_price
    assert variant_channel_listing.discounted_price != variant_channel_listing.price

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=variant_channel_listing,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert (
        checkout_line_info.variant_discounted_price == expected_discounted_variant_price
    )


def test_checkout_line_info_variant_discounted_price_without_listing(
    checkout_with_item_on_promotion,
):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()

    expected_discounted_variant_price = variant_channel_listing.discounted_price
    assert variant_channel_listing.discounted_price != variant_channel_listing.price

    variant.channel_listings.all().delete()

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=None,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert (
        checkout_line_info.variant_discounted_price == expected_discounted_variant_price
    )


def test_checkout_line_info_variant_discounted_price_when_listing_without_price(
    checkout_with_item_on_promotion,
):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()

    expected_discounted_variant_price = variant_channel_listing.discounted_price
    assert variant_channel_listing.discounted_price != variant_channel_listing.price

    variant_channel_listing.discounted_price_amount = None
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=variant_channel_listing,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert (
        checkout_line_info.variant_discounted_price == expected_discounted_variant_price
    )
