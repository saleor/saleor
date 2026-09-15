import datetime

from django.utils import timezone

from .....checkout import base_calculations
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....discount.models import VoucherCustomer
from .....plugins.manager import get_plugins_manager
from ....core.enums import VoucherRejectionReason
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_ADD_PROMO_CODE = """
    mutation($id: ID, $promoCode: String!) {
        checkoutAddPromoCode(id: $id, promoCode: $promoCode) {
            errors {
                field
                code
                voucherDetails {
                    reason
                    minSpent {
                        amount
                        currency
                    }
                    minCheckoutItemsQuantity
                    countries
                }
            }
        }
    }
"""

NO_PARAMS = {"minSpent": None, "minCheckoutItemsQuantity": None, "countries": None}


def _add_promo_code(client, checkout, promo_code):
    variables = {"id": to_global_id_or_none(checkout), "promoCode": promo_code}
    response = client.post_graphql(MUTATION_ADD_PROMO_CODE, variables)
    return get_graphql_content(response)["data"]["checkoutAddPromoCode"]


def _assert_single_error(data, expected_code, expected_details):
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "promoCode"
    assert error["code"] == expected_code.name
    assert error["voucherDetails"] == expected_details


def test_min_spent_not_reached(
    api_client, checkout_with_item, voucher_with_high_min_spent_amount
):
    # given
    min_spent = voucher_with_high_min_spent_amount.channel_listings.get().min_spent
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    subtotal = base_calculations.base_checkout_subtotal(
        lines, checkout_info.channel, checkout_with_item.currency
    )
    assert min_spent > subtotal

    # when
    data = _add_promo_code(
        api_client, checkout_with_item, voucher_with_high_min_spent_amount.code
    )

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.VOUCHER_NOT_APPLICABLE,
        NO_PARAMS
        | {
            "reason": VoucherRejectionReason.MIN_SPENT_NOT_REACHED.name,
            "minSpent": {
                "amount": float(min_spent.amount),
                "currency": min_spent.currency,
            },
        },
    )
    checkout_with_item.refresh_from_db(fields=("voucher_code",))
    assert checkout_with_item.voucher_code is None


def test_min_quantity_not_reached(api_client, checkout_with_item, voucher):
    # given
    min_quantity = 100
    assert checkout_with_item.lines.count() < min_quantity
    voucher.min_checkout_items_quantity = min_quantity
    voucher.save(update_fields=["min_checkout_items_quantity"])

    # when
    data = _add_promo_code(api_client, checkout_with_item, voucher.code)

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.VOUCHER_NOT_APPLICABLE,
        NO_PARAMS
        | {
            "reason": VoucherRejectionReason.MIN_QUANTITY_NOT_REACHED.name,
            "minCheckoutItemsQuantity": min_quantity,
        },
    )


def test_staff_only(api_client, checkout_with_item, voucher):
    # given
    voucher.only_for_staff = True
    voucher.save(update_fields=["only_for_staff"])

    # when
    data = _add_promo_code(api_client, checkout_with_item, voucher.code)

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.VOUCHER_NOT_APPLICABLE,
        NO_PARAMS | {"reason": VoucherRejectionReason.STAFF_ONLY.name},
    )


def test_already_used_by_customer(
    api_client, checkout_with_item, voucher, customer_user
):
    # given
    voucher.apply_once_per_customer = True
    voucher.save(update_fields=["apply_once_per_customer"])
    VoucherCustomer.objects.create(
        voucher_code=voucher.codes.get(), customer_email=customer_user.email
    )
    checkout_with_item.email = customer_user.email
    checkout_with_item.save(update_fields=["email"])

    # when
    data = _add_promo_code(api_client, checkout_with_item, voucher.code)

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.VOUCHER_NOT_APPLICABLE,
        NO_PARAMS | {"reason": VoucherRejectionReason.ALREADY_USED_BY_CUSTOMER.name},
    )


def test_no_eligible_lines(
    api_client, checkout_with_item, voucher_specific_product_type, product_list
):
    # given
    other_product = product_list[0]
    voucher_specific_product_type.products.set([other_product])
    checkout_products = {
        line.variant.product_id for line in checkout_with_item.lines.all()
    }
    assert other_product.pk not in checkout_products

    # when
    data = _add_promo_code(
        api_client, checkout_with_item, voucher_specific_product_type.code
    )

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.VOUCHER_NOT_APPLICABLE,
        NO_PARAMS | {"reason": VoucherRejectionReason.NO_ELIGIBLE_LINES.name},
    )


def test_shipping_not_required(
    api_client, checkout_without_shipping_required, voucher_shipping_type
):
    # when
    data = _add_promo_code(
        api_client, checkout_without_shipping_required, voucher_shipping_type.code
    )

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.VOUCHER_NOT_APPLICABLE,
        NO_PARAMS | {"reason": VoucherRejectionReason.SHIPPING_NOT_REQUIRED.name},
    )


def test_delivery_method_not_set(api_client, checkout_with_item, voucher_shipping_type):
    # given
    assert checkout_with_item.assigned_delivery is None

    # when
    data = _add_promo_code(api_client, checkout_with_item, voucher_shipping_type.code)

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.VOUCHER_NOT_APPLICABLE,
        NO_PARAMS | {"reason": VoucherRejectionReason.DELIVERY_METHOD_NOT_SET.name},
    )


def test_country_not_eligible(
    api_client,
    checkout_with_item,
    voucher_shipping_type,
    checkout_delivery,
    shipping_zone,
    address_usa,
):
    # given
    eligible_countries = ["IS"]
    voucher_shipping_type.countries = eligible_countries
    voucher_shipping_type.save(update_fields=["countries"])
    checkout_with_item.assigned_delivery = checkout_delivery(checkout_with_item)
    checkout_with_item.shipping_address = address_usa
    checkout_with_item.save(update_fields=["assigned_delivery", "shipping_address"])
    assert address_usa.country.code not in eligible_countries

    # when
    data = _add_promo_code(api_client, checkout_with_item, voucher_shipping_type.code)

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.VOUCHER_NOT_APPLICABLE,
        NO_PARAMS
        | {
            "reason": VoucherRejectionReason.COUNTRY_NOT_ELIGIBLE.name,
            "countries": eligible_countries,
        },
    )


def test_expired(api_client, checkout_with_item, voucher):
    # given
    voucher.start_date = timezone.now() - datetime.timedelta(days=10)
    voucher.end_date = timezone.now() - datetime.timedelta(days=1)
    voucher.save(update_fields=["start_date", "end_date"])

    # when
    data = _add_promo_code(api_client, checkout_with_item, voucher.code)

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.INVALID,
        NO_PARAMS | {"reason": VoucherRejectionReason.EXPIRED.name},
    )


def test_not_started(api_client, checkout_with_item, voucher):
    # given
    voucher.start_date = timezone.now() + datetime.timedelta(days=1)
    voucher.save(update_fields=["start_date"])

    # when
    data = _add_promo_code(api_client, checkout_with_item, voucher.code)

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.INVALID,
        NO_PARAMS | {"reason": VoucherRejectionReason.NOT_STARTED.name},
    )


def test_usage_limit_reached(api_client, checkout_with_item, voucher):
    # given
    voucher.usage_limit = 1
    voucher.save(update_fields=["usage_limit"])
    code = voucher.codes.get()
    code.used = 1
    code.save(update_fields=["used"])

    # when
    data = _add_promo_code(api_client, checkout_with_item, voucher.code)

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.INVALID,
        NO_PARAMS | {"reason": VoucherRejectionReason.USAGE_LIMIT_REACHED.name},
    )


def test_code_deactivated(api_client, checkout_with_item, voucher):
    # given
    code = voucher.codes.get()
    code.is_active = False
    code.save(update_fields=["is_active"])

    # when
    data = _add_promo_code(api_client, checkout_with_item, voucher.code)

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.INVALID,
        NO_PARAMS | {"reason": VoucherRejectionReason.CODE_DEACTIVATED.name},
    )


def test_not_available_in_channel(api_client, checkout_with_item, voucher):
    # given
    voucher.channel_listings.all().delete()

    # when
    data = _add_promo_code(api_client, checkout_with_item, voucher.code)

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.INVALID,
        NO_PARAMS | {"reason": VoucherRejectionReason.NOT_AVAILABLE_IN_CHANNEL.name},
    )


def test_unknown_code(api_client, checkout_with_item):
    # when
    data = _add_promo_code(api_client, checkout_with_item, "THIS-CODE-DOES-NOT-EXIST")

    # then
    _assert_single_error(
        data,
        CheckoutErrorCode.INVALID,
        NO_PARAMS | {"reason": VoucherRejectionReason.NOT_FOUND.name},
    )


def test_gift_card_error_carries_no_voucher_details(
    api_client, checkout_with_item, gift_card_expiry_date
):
    # given
    gift_card_expiry_date.expiry_date = datetime.date(1999, 1, 1)
    gift_card_expiry_date.save(update_fields=["expiry_date"])

    # when
    data = _add_promo_code(api_client, checkout_with_item, gift_card_expiry_date.code)

    # then
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["code"] == CheckoutErrorCode.INVALID.name
    assert error["voucherDetails"] is None


def test_applicable_voucher_reports_no_errors(api_client, checkout_with_item, voucher):
    # when
    data = _add_promo_code(api_client, checkout_with_item, voucher.code)

    # then
    assert data["errors"] == []
    checkout_with_item.refresh_from_db(fields=("voucher_code",))
    assert checkout_with_item.voucher_code == voucher.code
