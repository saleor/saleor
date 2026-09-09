import graphene
import pytest

from .....checkout.error_codes import OrderCreateFromCheckoutErrorCode
from .....discount.models import Voucher, VoucherCustomer
from .....order.models import Order
from ....core.enums import PromoCodeRejectionReason
from ....tests.utils import get_graphql_content

MUTATION_ORDER_CREATE_FROM_CHECKOUT = """
mutation orderCreateFromCheckout($id: ID!) {
    orderCreateFromCheckout(id: $id) {
        order {
            id
        }
        errors {
            field
            code
            promoCodeDetails {
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


@pytest.fixture
def checkout_ready_for_order(
    checkout_with_voucher_percentage, address, checkout_delivery
):
    checkout = checkout_with_voucher_percentage
    checkout.email = "customer@example.com"
    checkout.shipping_address = address
    checkout.billing_address = address
    checkout.assigned_delivery = checkout_delivery(checkout)
    checkout.save()
    return checkout


def _create_order(client, checkout):
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = client.post_graphql(MUTATION_ORDER_CREATE_FROM_CHECKOUT, variables)
    return get_graphql_content(response)["data"]["orderCreateFromCheckout"]


def _assert_rejected(data, expected_reason):
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "voucherCode"
    assert error["code"] == OrderCreateFromCheckoutErrorCode.VOUCHER_NOT_APPLICABLE.name
    assert error["promoCodeDetails"] == NO_PARAMS | {"reason": expected_reason.name}
    assert data["order"] is None
    assert Order.objects.exists() is False


def test_voucher_no_longer_available(
    app_api_client, permission_handle_checkouts, checkout_ready_for_order
):
    """Report the reason from the pre-order checkout validation."""
    # given
    app_api_client.app.permissions.add(permission_handle_checkouts)
    assert checkout_ready_for_order.voucher_code is not None
    Voucher.objects.all().delete()

    # when
    data = _create_order(app_api_client, checkout_ready_for_order)

    # then
    _assert_rejected(data, PromoCodeRejectionReason.NO_LONGER_AVAILABLE)


def test_voucher_already_used_by_customer(
    app_api_client,
    permission_handle_checkouts,
    checkout_ready_for_order,
    voucher_percentage,
):
    """Report the reason from a `NotApplicable` raised while placing the order."""
    # given
    app_api_client.app.permissions.add(permission_handle_checkouts)
    voucher_percentage.apply_once_per_customer = True
    voucher_percentage.save(update_fields=["apply_once_per_customer"])
    VoucherCustomer.objects.create(
        voucher_code=voucher_percentage.codes.get(),
        customer_email=checkout_ready_for_order.email,
    )

    # when
    data = _create_order(app_api_client, checkout_ready_for_order)

    # then
    _assert_rejected(data, PromoCodeRejectionReason.ALREADY_USED_BY_CUSTOMER)
