import json
from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

EXCLUDE_PRODUCTS_MUTATION = """
    mutation shippingPriceRemoveProductFromExclude(
        $id: ID!, $input:ShippingPriceExcludeProductsInput!
        ) {
        shippingPriceExcludeProducts(
            id: $id
            input: $input) {
            errors {
                field
                code
            }
            shippingMethod {
                id
                excludedProducts(first:10){
                   totalCount
                   edges{
                     node{
                       id
                     }
                   }
                }
            }
        }
    }
"""


@pytest.mark.parametrize("requestor", ["staff", "app"])
def test_exclude_products_for_shipping_method_only_products(
    requestor,
    app_api_client,
    shipping_method,
    product_list,
    staff_api_client,
    permission_manage_shipping,
):
    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    product_ids = [graphene.Node.to_global_id("Product", p.pk) for p in product_list]
    variables = {"id": shipping_method_id, "input": {"products": product_ids}}
    response = api.post_graphql(
        EXCLUDE_PRODUCTS_MUTATION, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    shipping_method = content["data"]["shippingPriceExcludeProducts"]["shippingMethod"]
    excluded_products = shipping_method["excludedProducts"]
    total_count = excluded_products["totalCount"]
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert len(product_ids) == total_count
    assert excluded_product_ids == set(product_ids)


@pytest.mark.parametrize("requestor", ["staff", "app"])
def test_exclude_products_for_shipping_method_already_has_excluded_products(
    requestor,
    shipping_method,
    product_list,
    product,
    staff_api_client,
    permission_manage_shipping,
    app_api_client,
):
    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    shipping_method.excluded_products.add(product, product_list[0])
    product_ids = [graphene.Node.to_global_id("Product", p.pk) for p in product_list]
    variables = {"id": shipping_method_id, "input": {"products": product_ids}}
    response = api.post_graphql(
        EXCLUDE_PRODUCTS_MUTATION, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    shipping_method = content["data"]["shippingPriceExcludeProducts"]["shippingMethod"]
    excluded_products = shipping_method["excludedProducts"]
    total_count = excluded_products["totalCount"]
    expected_product_ids = product_ids
    expected_product_ids.append(graphene.Node.to_global_id("Product", product.pk))
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert len(expected_product_ids) == total_count
    assert excluded_product_ids == set(expected_product_ids)


@freeze_time("2022-05-12 12:00:00")
@pytest.mark.parametrize("requestor", ["staff", "app"])
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_exclude_products_for_shipping_method_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    requestor,
    any_webhook,
    app_api_client,
    shipping_method,
    product_list,
    staff_api_client,
    permission_manage_shipping,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    product_ids = [graphene.Node.to_global_id("Product", p.pk) for p in product_list]
    variables = {"id": shipping_method_id, "input": {"products": product_ids}}

    # when
    response = api.post_graphql(
        EXCLUDE_PRODUCTS_MUTATION, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    issuer = SimpleLazyObject(lambda: api.user if requestor == "staff" else api.app)

    # then
    assert content["data"]["shippingPriceExcludeProducts"]["shippingMethod"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": shipping_method_id,
                "meta": generate_meta(requestor_data=generate_requestor(issuer)),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.SHIPPING_PRICE_UPDATED,
        [any_webhook],
        shipping_method,
        issuer,
    )
