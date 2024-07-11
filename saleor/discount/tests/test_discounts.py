from datetime import timedelta
from decimal import Decimal

import graphene
import pytest
from django.utils import timezone
from prices import Money, TaxedMoney

from ...checkout.fetch import CheckoutLineInfo
from ...discount.interface import VariantPromotionRuleInfo
from .. import DiscountValueType, RewardValueType, VoucherType
from ..models import (
    NotApplicable,
    Voucher,
    VoucherChannelListing,
    VoucherCode,
    VoucherCustomer,
)
from ..utils.promotion import (
    get_discount_name,
    get_discount_translated_name,
)
from ..utils.voucher import (
    _get_the_cheapest_line,
    activate_voucher_code,
    add_voucher_usage_by_customer,
    deactivate_voucher_code,
    decrease_voucher_code_usage_value,
    increase_voucher_code_usage_value,
    is_order_level_voucher,
    remove_voucher_usage_by_customer,
    validate_voucher,
)


def test_valid_voucher_min_spent_amount(channel_USD):
    voucher = Voucher.objects.create(
        type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.FIXED,
    )
    VoucherCode.objects.create(code="unique", voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, "USD"),
        min_spent=Money(7, "USD"),
    )
    value = Money(7, "USD")

    voucher.validate_min_spent(value, channel_USD)


def test_valid_voucher_min_spent_amount_not_reached(channel_USD):
    voucher = Voucher.objects.create(
        type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.FIXED,
    )
    VoucherCode.objects.create(code="unique", voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, "USD"),
        min_spent=Money(7, "USD"),
    )
    value = Money(5, "USD")

    with pytest.raises(NotApplicable):
        voucher.validate_min_spent(value, channel_USD)


def test_valid_voucher_min_spent_amount_voucher_not_assigned_to_channel(
    channel_USD, channel_PLN
):
    voucher = Voucher.objects.create(
        type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.FIXED,
    )
    VoucherCode.objects.create(code="unique", voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
        min_spent=(Money(5, channel_USD.currency_code)),
    )
    price = Money(10, channel_PLN.currency_code)
    total_price = TaxedMoney(net=price, gross=price)
    with pytest.raises(NotApplicable):
        voucher.validate_min_spent(total_price, channel_PLN)


def test_valid_voucher_min_checkout_items_quantity(voucher):
    voucher.min_checkout_items_quantity = 3
    voucher.save()

    with pytest.raises(NotApplicable) as e:
        voucher.validate_min_checkout_items_quantity(2)

    assert (
        str(e.value)
        == "This offer is only valid for orders with a minimum of 3 quantity."
    )


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_percentage_discounts(product, channel_USD, catalogue_promotion_without_rules):
    # given
    variant = product.variants.get()
    reward_value = Decimal("50")
    rule = catalogue_promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", variant.product.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=reward_value,
    )

    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=Decimal("5"),
        currency=channel_USD.currency_code,
    )
    price = Decimal("10")

    # when
    final_price = variant.get_price(
        variant_channel_listing, price, promotion_rules=[rule]
    )

    # then
    assert final_price.amount == price - reward_value / 100 * price


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_fixed_discounts(product, channel_USD, catalogue_promotion_without_rules):
    # given
    variant = product.variants.get()
    reward_value = Decimal("5")
    rule = catalogue_promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", variant.product.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )

    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=Decimal("1"),
        currency=channel_USD.currency_code,
    )
    price = Decimal("10")

    # when
    final_price = variant.get_price(
        variant_channel_listing, price, promotion_rules=[rule]
    )

    # then
    assert final_price.amount == price - reward_value


def test_voucher_queryset_active(voucher, channel_USD):
    vouchers = Voucher.objects.all()
    assert vouchers.count() == 1
    active_vouchers = Voucher.objects.active_in_channel(
        date=timezone.now() - timedelta(days=1), channel_slug=channel_USD.slug
    )
    assert active_vouchers.count() == 0


def test_voucher_queryset_active_in_channel(voucher, channel_USD):
    vouchers = Voucher.objects.all()
    assert vouchers.count() == 1
    active_vouchers = Voucher.objects.active_in_channel(
        date=timezone.now(), channel_slug=channel_USD.slug
    )
    assert active_vouchers.count() == 1


def test_voucher_queryset_active_in_other_channel(voucher, channel_PLN):
    vouchers = Voucher.objects.all()
    assert vouchers.count() == 1
    active_vouchers = Voucher.objects.active_in_channel(
        date=timezone.now(), channel_slug=channel_PLN.slug
    )
    assert active_vouchers.count() == 0


def test_increase_voucher_usage(channel_USD):
    code = ("unique",)
    voucher = Voucher.objects.create(
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=DiscountValueType.FIXED,
        usage_limit=100,
    )
    code_instance = VoucherCode.objects.create(code=code, voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
    )
    increase_voucher_code_usage_value(code_instance)
    code_instance.refresh_from_db(fields=["used"])
    assert code_instance.used == 1


def test_decrease_voucher_usage(channel_USD):
    code = "unique"
    voucher = Voucher.objects.create(
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=DiscountValueType.FIXED,
        usage_limit=100,
    )
    code_instance = VoucherCode.objects.create(code=code, voucher=voucher, used=10)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
    )
    decrease_voucher_code_usage_value(code_instance)
    code_instance.refresh_from_db(fields=["used"])
    assert code_instance.used == 9


def test_deactivate_voucher_code(voucher):
    # given
    code_instance = voucher.codes.first()

    # when
    deactivate_voucher_code(code_instance)

    # then
    code_instance.refresh_from_db(fields=["is_active"])
    assert code_instance.is_active is False


def test_activate_voucher_code(voucher):
    # given
    code_instance = voucher.codes.first()
    code_instance.is_active = False
    code_instance.save(update_fields=["is_active"])

    # when
    activate_voucher_code(code_instance)

    # then
    code_instance.refresh_from_db(fields=["is_active"])
    assert code_instance.is_active is True


def test_add_voucher_usage_by_customer(voucher, customer_user):
    # given
    voucher_customer_count = VoucherCustomer.objects.all().count()
    code = voucher.codes.first()

    # when
    add_voucher_usage_by_customer(code, customer_user.email)

    # then
    assert VoucherCustomer.objects.all().count() == voucher_customer_count + 1
    voucherCustomer = VoucherCustomer.objects.first()
    assert voucherCustomer.voucher_code == code
    assert voucherCustomer.customer_email == customer_user.email


def test_add_voucher_usage_by_customer_raise_not_applicable(voucher_customer):
    # given
    code = voucher_customer.voucher_code

    customer_email = voucher_customer.customer_email

    # when & then
    with pytest.raises(NotApplicable):
        add_voucher_usage_by_customer(code, customer_email)


def test_add_voucher_usage_by_customer_without_customer_email(voucher):
    # given
    code = voucher.codes.first()

    # when & then
    with pytest.raises(NotApplicable):
        add_voucher_usage_by_customer(code, None)


def test_remove_voucher_usage_by_customer(voucher_customer):
    # given
    voucher_customer_count = VoucherCustomer.objects.all().count()
    code = voucher_customer.voucher_code
    customer_email = voucher_customer.customer_email

    # when
    remove_voucher_usage_by_customer(code, customer_email)

    # then
    assert VoucherCustomer.objects.all().count() == voucher_customer_count - 1


def test_remove_voucher_usage_by_customer_not_exists(voucher):
    # given
    code = voucher.codes.first()

    # when & then
    remove_voucher_usage_by_customer(code, "fake@exmaimpel.com")


@pytest.mark.parametrize(
    (
        "total",
        "min_spent_amount",
        "total_quantity",
        "min_checkout_items_quantity",
        "discount_value_type",
    ),
    [
        (20, 20, 2, 2, DiscountValueType.PERCENTAGE),
        (20, None, 2, None, DiscountValueType.PERCENTAGE),
        (20, 20, 2, 2, DiscountValueType.FIXED),
        (20, None, 2, None, DiscountValueType.FIXED),
    ],
)
def test_validate_voucher(
    total,
    min_spent_amount,
    total_quantity,
    min_checkout_items_quantity,
    discount_value_type,
    channel_USD,
):
    voucher = Voucher.objects.create(
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=discount_value_type,
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    VoucherCode.objects.create(code="unique", voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(50, channel_USD.currency_code),
        min_spent_amount=min_spent_amount,
    )
    total_price = Money(total, "USD")
    validate_voucher(
        voucher, total_price, total_quantity, "test@example.com", channel_USD, None
    )


def test_validate_staff_voucher_for_anonymous(
    channel_USD,
):
    voucher = Voucher.objects.create(
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=DiscountValueType.PERCENTAGE,
        only_for_staff=True,
    )
    VoucherCode.objects.create(code="unique", voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(50, channel_USD.currency_code),
    )
    total_price = Money(100, "USD")
    price = TaxedMoney(gross=total_price, net=total_price)
    with pytest.raises(NotApplicable):
        validate_voucher(voucher, price, 2, "test@example.com", channel_USD, None)


def test_validate_staff_voucher_for_normal_customer(channel_USD, customer_user):
    voucher = Voucher.objects.create(
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=DiscountValueType.PERCENTAGE,
        only_for_staff=True,
    )
    VoucherCode.objects.create(code="unique", voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(50, channel_USD.currency_code),
    )
    total_price = Money(100, "USD")
    price = TaxedMoney(gross=total_price, net=total_price)
    with pytest.raises(NotApplicable):
        validate_voucher(
            voucher, price, 2, customer_user.email, channel_USD, customer_user
        )


def test_validate_staff_voucher_for_staff_customer(channel_USD, staff_user):
    voucher = Voucher.objects.create(
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=DiscountValueType.PERCENTAGE,
        only_for_staff=True,
    )
    VoucherCode.objects.create(code="unique", voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(50, channel_USD.currency_code),
    )
    total_price = Money(100, "USD")
    price = TaxedMoney(gross=total_price, net=total_price)

    validate_voucher(voucher, price, 2, staff_user.email, channel_USD, staff_user)


@pytest.mark.parametrize(
    (
        "total",
        "min_spent_amount",
        "total_quantity",
        "min_checkout_items_quantity",
        "discount_value",
        "discount_value_type",
    ),
    [
        (20, 50, 2, 10, 50, DiscountValueType.PERCENTAGE),
        (20, 50, 2, None, 50, DiscountValueType.PERCENTAGE),
        (20, None, 2, 10, 50, DiscountValueType.FIXED),
    ],
)
def test_validate_voucher_not_applicable(
    total,
    min_spent_amount,
    total_quantity,
    min_checkout_items_quantity,
    discount_value,
    discount_value_type,
    channel_USD,
):
    voucher = Voucher.objects.create(
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=discount_value_type,
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    VoucherCode.objects.create(code="unique", voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(50, channel_USD.currency_code),
        min_spent_amount=min_spent_amount,
    )
    total_price = Money(total, "USD")

    with pytest.raises(NotApplicable):
        validate_voucher(
            voucher, total_price, total_quantity, "test@example.com", channel_USD, None
        )


def test_validate_voucher_not_applicable_once_per_customer(
    voucher, customer_user, channel_USD
):
    # given
    voucher.apply_once_per_customer = True
    voucher.save()

    code = voucher.codes.first()

    VoucherCustomer.objects.create(
        voucher_code=code, customer_email=customer_user.email
    )
    price = Money(0, "USD")
    total_price = TaxedMoney(net=price, gross=price)

    # when & then
    with pytest.raises(NotApplicable):
        validate_voucher(
            voucher,
            total_price,
            0,
            customer_user.email,
            channel_USD,
            customer_user,
        )


date_time_now = timezone.now()


def test_get_discount_name_only_rule_name(catalogue_promotion):
    # given
    promotion = catalogue_promotion
    promotion.name = ""
    promotion.save(update_fields=["name"])

    rule = promotion.rules.first()

    # when
    name = get_discount_name(rule, promotion)

    # then
    assert name == rule.name


def test_get_discount_name_only_rule_promotion_name(catalogue_promotion):
    # given
    promotion = catalogue_promotion
    rule = promotion.rules.first()
    rule.name = ""
    rule.save(update_fields=["name"])

    # when
    name = get_discount_name(rule, promotion)

    # then
    assert name == promotion.name


def test_get_discount_name_rule_and_promotion_name(catalogue_promotion):
    # given
    promotion = catalogue_promotion
    rule = promotion.rules.first()

    # when
    name = get_discount_name(rule, promotion)

    # then
    assert name == f"{promotion.name}: {rule.name}"


def test_get_discount_name_empty_names(catalogue_promotion):
    # given
    promotion = catalogue_promotion
    rule = promotion.rules.first()

    rule.name = ""
    rule.save(update_fields=["name"])

    promotion.name = ""
    promotion.save(update_fields=["name"])

    # when
    name = get_discount_name(rule, promotion)

    # then
    assert name == ""


def test_get_discount_translated_name_only_rule_translation(rule_info):
    # given
    rule_info_data = rule_info._asdict()
    rule_info_data["promotion_translation"] = None
    rule_info = VariantPromotionRuleInfo(**rule_info_data)

    # when
    translated_name = get_discount_translated_name(rule_info)

    # then
    assert translated_name == rule_info.rule_translation.name


def test_get_discount_translated_name_only_rule_promotion_translation(rule_info):
    # given
    rule_info_data = rule_info._asdict()
    rule_info_data["rule_translation"] = None
    rule_info = VariantPromotionRuleInfo(**rule_info_data)

    # when
    translated_name = get_discount_translated_name(rule_info)

    # then
    assert translated_name == rule_info.promotion_translation.name


def test_get_discount_translated_name_rule_and_promotion_translations(rule_info):
    # when
    translated_name = get_discount_translated_name(rule_info)

    # then
    assert (
        translated_name
        == f"{rule_info.promotion_translation.name}: {rule_info.rule_translation.name}"
    )


def test_get_discount_translated_name_no_translations(rule_info):
    # given
    rule_info_data = rule_info._asdict()
    rule_info_data["promotion_translation"] = None
    rule_info_data["rule_translation"] = None
    rule_info = VariantPromotionRuleInfo(**rule_info_data)

    # when
    translated_name = get_discount_translated_name(rule_info)

    # then
    assert translated_name is None


def test_is_order_level_voucher(voucher):
    # given
    voucher.type = VoucherType.ENTIRE_ORDER
    voucher.save(update_fields=["type"])

    # when
    result = is_order_level_voucher(voucher)

    # then
    assert result is True


def test_is_order_level_voucher_apply_once_per_order(voucher):
    # given
    voucher.type = VoucherType.ENTIRE_ORDER
    voucher.apply_once_per_order = True
    voucher.save(update_fields=["type", "apply_once_per_order"])

    # when
    result = is_order_level_voucher(voucher)

    # then
    assert result is False


def test_is_order_level_voucher_no_voucher(voucher):
    # when
    result = is_order_level_voucher(None)

    # then
    assert result is False


@pytest.mark.parametrize(
    "voucher_type", [VoucherType.SPECIFIC_PRODUCT, VoucherType.SHIPPING]
)
def test_is_order_level_voucher_another_type(voucher_type, voucher):
    # given
    voucher.type = voucher_type
    voucher.save(update_fields=["type"])

    # when
    result = is_order_level_voucher(voucher)

    # then
    assert result is False


def test_get_the_cheapest_line_no_lines_provided():
    # when
    line_info = _get_the_cheapest_line(None)
    # then
    assert line_info is None


def test_get_the_cheapest_line(checkout_with_items, channel_USD):
    # given
    lines = [
        CheckoutLineInfo(
            line=line,
            channel_listing=line.variant.channel_listings.first(),
            collections=[],
            product=line.variant.product,
            variant=line.variant,
            discounts=list(line.discounts.all()),
            rules_info=[],
            product_type=line.variant.product.product_type,
            channel=channel_USD,
            voucher=None,
            voucher_code=None,
        )
        for line in checkout_with_items.lines.all()
    ]
    # when
    line_info = _get_the_cheapest_line(lines)
    # then
    assert line_info == lines[0]
