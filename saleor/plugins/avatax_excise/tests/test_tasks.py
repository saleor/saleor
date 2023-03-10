from dataclasses import asdict
from decimal import Decimal
from urllib.parse import urljoin

import pytest

from ....order import OrderEvents
from ..tasks import api_post_request_task
from ..utils import (
    AvataxConfiguration,
    get_api_url,
    get_metadata_key,
    get_order_request_data,
    get_order_tax_data,
)

config = AvataxConfiguration(
    username_or_account="test",
    password_or_license="test",
    company_name="test",
    use_sandbox=True,
    autocommit=True,
)


@pytest.mark.vcr
def test_api_post_request_task_with_invalid_productcodes(
    product,
    cigar_product_type,
    order_with_lines,
    address_usa_va,
    shipping_zone,
):

    order_with_lines.shipping_address = address_usa_va
    order_with_lines.shipping_method = shipping_zone.shipping_methods.get()
    shipping_method = shipping_zone.shipping_methods.get()
    shipping_method.price_amount = 0
    shipping_method.save()
    order_with_lines.shipping_method = shipping_method

    product.product_type = cigar_product_type
    product.save()

    variant = product.variants.first()
    variant.sku = "FAKEPROD"
    variant.price_amount = Decimal(170)
    variant.save()

    for order_line in order_with_lines.lines.all():
        order_line.product_name = product.name
        order_line.variant_name = variant.name
        order_line.product_sku = variant.sku
        order_line.variant = variant
        order_line.save()

    order_with_lines.save()

    request_data = get_order_request_data(order_with_lines, config)

    base_url = get_api_url(config.use_sandbox)
    transaction_url = urljoin(
        base_url,
        "AvaTaxExcise/transactions/create",
    )
    commit_url = urljoin(
        base_url,
        "AvaTaxExcise/transactions/{}/commit",
    )

    response = api_post_request_task(
        transaction_url,
        asdict(request_data),
        asdict(config),
        order_with_lines.id,
        commit_url,
    )

    assert response is None
    msg = 'Product "FAKEPROD" does not exist'

    assert order_with_lines.events.count() == 1
    event = order_with_lines.events.get()
    assert event.type == OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    assert msg in event.parameters["message"]


@pytest.mark.vcr
def test_api_post_request_task_with_valid_productcodes(
    product,
    cigar_product_type,
    order_with_lines,
    address_usa_va,
    shipping_zone,
):

    order_with_lines.shipping_address = address_usa_va
    order_with_lines.shipping_method = shipping_zone.shipping_methods.get()
    shipping_method = shipping_zone.shipping_methods.get()
    shipping_method.price_amount = 0
    shipping_method.save()
    order_with_lines.shipping_method = shipping_method

    product.product_type = cigar_product_type
    product.save()

    variant = product.variants.first()
    variant.sku = "202015500"
    variant.price_amount = Decimal(170)
    variant.save()

    for order_line in order_with_lines.lines.all():
        order_line.product_name = product.name
        order_line.variant_name = variant.name
        order_line.product_sku = variant.sku
        order_line.variant = variant
        order_line.save()

    order_with_lines.save()

    request_data = get_order_request_data(order_with_lines, config)

    base_url = get_api_url(config.use_sandbox)
    transaction_url = urljoin(
        base_url,
        "AvaTaxExcise/transactions/create",
    )
    commit_url = urljoin(
        base_url,
        "AvaTaxExcise/transactions/{}/commit",
    )

    api_post_request_task(
        transaction_url,
        asdict(request_data),
        asdict(config),
        order_with_lines.id,
        commit_url,
    )

    expected_event_msg = (
        "Order committed to Avatax Excise. " f"Order ID: {order_with_lines.id}"
    )
    assert order_with_lines.events.count() == 1
    event = order_with_lines.events.get()
    assert event.type == OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    assert event.parameters["message"] == expected_event_msg

    order_with_lines.refresh_from_db()
    taxes_metadata = order_with_lines.metadata.get(get_metadata_key("itemized_taxes"))

    sales_tax = order_with_lines.metadata.get(get_metadata_key("sales_tax"))
    other_tax = order_with_lines.metadata.get(get_metadata_key("other_tax"))

    assert taxes_metadata is not None
    assert len(taxes_metadata) > 0
    assert sales_tax >= 0
    assert other_tax >= 0


def test_api_request_task_order_doesnt_have_any_lines_with_taxes_to_calculate(
    order_with_lines, shipping_zone, monkeypatch
):
    mock_api_post_request = {"error": {"message": "Wrong credentials"}}
    monkeypatch.setattr(
        "saleor.plugins.avatax.tasks.api_post_request",
        lambda *_: mock_api_post_request,
    )

    request_data = {}

    base_url = get_api_url(config.use_sandbox)
    transaction_url = urljoin(
        base_url,
        "AvaTaxExcise/transactions/create",
    )
    commit_url = urljoin(
        base_url,
        "AvaTaxExcise/transactions/{}/commit",
    )

    api_post_request_task(
        transaction_url,
        request_data,
        asdict(config),
        order_with_lines.id,
        commit_url,
    )

    assert order_with_lines.events.count() == 1
    event = order_with_lines.events.get()
    assert event.type == OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    expected_msg = (
        "The order doesn't have any line which should be " "sent to Avatax Excise."
    )
    assert event.parameters["message"] == expected_msg


def test_api_request_task_order_empty_data(order):
    # given
    request_data = {}

    base_url = get_api_url(config.use_sandbox)
    transaction_url = urljoin(
        base_url,
        "AvaTaxExcise/transactions/create",
    )
    commit_url = urljoin(
        base_url,
        "AvaTaxExcise/transactions/{}/commit",
    )

    # when
    api_post_request_task(
        transaction_url,
        request_data,
        asdict(config),
        order.id,
        commit_url,
    )

    # then
    assert order.events.count() == 1
    event = order.events.get()
    assert event.type == OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    expected_msg = (
        "The order doesn't have any line which should be " "sent to Avatax Excise."
    )
    assert event.parameters["message"] == expected_msg


def test_get_order_request_data_order_without_lines(order):
    # when
    data = get_order_request_data(order, config)

    # then
    assert data == {}


def test_get_order_tax_data_for_empty_data(order):
    # when
    data = get_order_tax_data(order, config)

    # then
    assert data is None
