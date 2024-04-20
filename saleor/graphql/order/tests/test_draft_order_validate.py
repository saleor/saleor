from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
import pytz
from django.core.exceptions import ValidationError

from ....order.error_codes import OrderErrorCode
from ....plugins.manager import get_plugins_manager
from ....product.models import ProductVariant
from ..utils import validate_draft_order


def test_validate_draft_order(draft_order):
    # should not raise any errors
    assert (
        validate_draft_order(
            draft_order,
            draft_order.lines.all(),
            "US",
            get_plugins_manager(allow_replica=False),
        )
        is None
    )


def test_validate_draft_order_without_sku(draft_order):
    ProductVariant.objects.update(sku=None)
    draft_order.lines.update(product_sku=None)
    # should not raise any errors
    assert (
        validate_draft_order(
            draft_order,
            draft_order.lines.all(),
            "US",
            get_plugins_manager(allow_replica=False),
        )
        is None
    )


def test_validate_draft_order_wrong_shipping(draft_order):
    order = draft_order
    shipping_zone = order.shipping_method.shipping_zone
    shipping_zone.countries = ["DE"]
    shipping_zone.save()
    assert order.shipping_address.country.code not in shipping_zone.countries
    with pytest.raises(ValidationError) as e:
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )
    msg = "Shipping method is not valid for chosen shipping address"
    assert e.value.error_dict["shipping"][0].message == msg


def test_validate_draft_order_no_order_lines(order, shipping_method):
    order.shipping_method = shipping_method
    with pytest.raises(ValidationError) as e:
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )
    msg = "Could not create order without any products."
    assert e.value.error_dict["lines"][0].message == msg


def test_validate_draft_order_non_existing_variant(draft_order):
    order = draft_order
    line = order.lines.first()
    variant = line.variant
    variant.delete()
    line.refresh_from_db()
    assert line.variant is None

    with pytest.raises(ValidationError) as e:
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )
    msg = "Could not create orders with non-existing products."
    assert e.value.error_dict["lines"][0].message == msg


def test_validate_draft_order_with_unpublished_product(draft_order):
    order = draft_order
    line = order.lines.first()
    variant = line.variant
    product_channel_listing = variant.product.channel_listings.get()
    product_channel_listing.is_published = False
    product_channel_listing.save(update_fields=["is_published"])
    line.refresh_from_db()

    with pytest.raises(ValidationError) as e:
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )
    msg = "Can't finalize draft with unpublished product."
    error = e.value.error_dict["lines"][0]

    assert error.message == msg
    assert error.code == OrderErrorCode.PRODUCT_NOT_PUBLISHED.value


def test_validate_draft_order_with_unavailable_for_purchase_product(draft_order):
    order = draft_order
    line = order.lines.first()
    variant = line.variant
    variant.product.channel_listings.update(available_for_purchase_at=None)
    line.refresh_from_db()

    with pytest.raises(ValidationError) as e:
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )
    msg = "Can't finalize draft with product unavailable for purchase."
    error = e.value.error_dict["lines"][0]

    assert error.message == msg
    assert error.code == OrderErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.value


def test_validate_draft_order_with_product_available_for_purchase_in_future(
    draft_order,
):
    order = draft_order
    line = order.lines.first()
    variant = line.variant
    variant.product.channel_listings.update(
        available_for_purchase_at=datetime.now(pytz.UTC) + timedelta(days=2)
    )
    line.refresh_from_db()

    with pytest.raises(ValidationError) as e:
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )
    msg = "Can't finalize draft with product unavailable for purchase."
    error = e.value.error_dict["lines"][0]

    assert error.message == msg
    assert error.code == OrderErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.value


def test_validate_draft_order_out_of_stock_variant(draft_order):
    order = draft_order
    line = order.lines.first()
    variant = line.variant

    stock = variant.stocks.get()
    stock.quantity = 0
    stock.save(update_fields=["quantity"])

    with pytest.raises(ValidationError) as e:
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )
    msg = "Insufficient product stock."
    assert e.value.error_dict["lines"][0].message == msg


def test_validate_draft_order_no_shipping_address(draft_order):
    order = draft_order
    order.shipping_address = None

    with pytest.raises(ValidationError) as e:
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )
    error = e.value.error_dict["order"][0]
    assert error.message == "Can't finalize draft with no shipping address."
    assert error.code == OrderErrorCode.ORDER_NO_SHIPPING_ADDRESS.value


def test_validate_draft_order_no_billing_address(draft_order):
    order = draft_order
    order.billing_address = None

    with pytest.raises(ValidationError) as e:
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )
    error = e.value.error_dict["order"][0]
    assert error.message == "Can't finalize draft with no billing address."
    assert error.code == OrderErrorCode.BILLING_ADDRESS_NOT_SET.value


def test_validate_draft_order_no_shipping_method(draft_order):
    order = draft_order
    order.shipping_method = None

    with pytest.raises(ValidationError) as e:
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )
    error = e.value.error_dict["shipping"][0]
    assert error.message == "Shipping method is required."
    assert error.code == OrderErrorCode.SHIPPING_METHOD_REQUIRED.value


@patch("saleor.graphql.order.utils.is_shipping_required")
def test_validate_draft_order_no_shipping_method_shipping_not_required(
    mocked_is_shipping_required, draft_order
):
    order = draft_order
    order.shipping_method = None
    mocked_is_shipping_required.return_value = False

    assert (
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )
        is None
    )


@patch("saleor.graphql.order.utils.is_shipping_required")
def test_validate_draft_order_no_shipping_address_no_method_shipping_not_required(
    mocked_is_shipping_required,
    draft_order,
):
    order = draft_order
    order.shipping_method = None
    order.shipping_address = None
    mocked_is_shipping_required.return_value = False

    assert (
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )
        is None
    )


def test_validate_draft_order_voucher(draft_order_with_voucher):
    # given
    order = draft_order_with_voucher
    order.voucher.channel_listings.all().delete()

    # when & then
    with pytest.raises(ValidationError) as e:
        validate_draft_order(
            order, order.lines.all(), "US", get_plugins_manager(allow_replica=False)
        )

    error = e.value.error_dict["voucher"][0]
    assert error.code == OrderErrorCode.INVALID_VOUCHER.value
