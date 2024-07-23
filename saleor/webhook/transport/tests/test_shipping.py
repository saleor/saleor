from ....checkout.utils import get_or_create_checkout_metadata
from ...payloads import (
    generate_checkout_payload,
    generate_excluded_shipping_methods_for_checkout_payload,
)
from ..shipping import (
    get_cache_data_for_exclude_shipping_methods,
    get_cache_data_for_shipping_list_methods_for_checkout,
)


def test_get_cache_data_for_shipping_list_methods_for_checkout(checkout_with_items):
    # given
    metadata = get_or_create_checkout_metadata(checkout_with_items)
    metadata.store_value_in_private_metadata({"external_app_shipping_id": "something"})
    metadata.save()
    payload_str = generate_checkout_payload(checkout_with_items)
    assert "last_change" in payload_str
    assert "meta" in payload_str
    assert "external_app_shipping_id" in payload_str

    # when
    cache_data = get_cache_data_for_shipping_list_methods_for_checkout(payload_str)

    # then
    assert "last_change" not in cache_data[0]
    assert "meta" not in cache_data[0]
    assert "external_app_shipping_id" not in cache_data[0]["private_metadata"]


def test_get_cache_data_for_exclude_shipping_methods(checkout_with_items):
    # given
    payload_str = generate_excluded_shipping_methods_for_checkout_payload(
        checkout_with_items, []
    )
    assert "last_change" in payload_str
    assert "meta" in payload_str

    # when
    cache_data = get_cache_data_for_exclude_shipping_methods(payload_str)

    # then
    assert "last_change" not in cache_data
    assert "meta" not in cache_data
