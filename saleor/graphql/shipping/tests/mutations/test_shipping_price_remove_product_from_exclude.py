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

REMOVE_PRODUCTS_FROM_EXCLUDED_PRODUCTS_MUTATION = """
    mutation shippingPriceRemoveProductFromExclude(
        $id: ID!, $products: [ID!]!
        ) {
        shippingPriceRemoveProductFromExclude(
            id: $id
            products: $products) {
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
def test_remove_products_from_excluded_products_for_shipping_method_delete_all_products(
    requestor,
    shipping_method,
    product_list,
    staff_api_client,
    permission_manage_shipping,
    app_api_client,
):
    # given
    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    shipping_method.excluded_products.set(product_list)

    product_ids = [graphene.Node.to_global_id("Product", p.pk) for p in product_list]
    variables = {"id": shipping_method_id, "products": product_ids}

    # when
    response = api.post_graphql(
        REMOVE_PRODUCTS_FROM_EXCLUDED_PRODUCTS_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)
    shipping_method = content["data"]["shippingPriceRemoveProductFromExclude"][
        "shippingMethod"
    ]
    excluded_products = shipping_method["excludedProducts"]
    total_count = excluded_products["totalCount"]
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert total_count == 0
    assert len(excluded_product_ids) == 0


@pytest.mark.parametrize("requestor", ["staff", "app"])
def test_remove_products_from_excluded_products_for_shipping_method(
    requestor,
    shipping_method,
    product_list,
    staff_api_client,
    permission_manage_shipping,
    product,
    app_api_client,
):
    # given
    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    shipping_method.excluded_products.set(product_list)
    shipping_method.excluded_products.add(product)

    product_ids = [
        graphene.Node.to_global_id("Product", product.pk),
    ]
    variables = {"id": shipping_method_id, "products": product_ids}

    # when
    response = api.post_graphql(
        REMOVE_PRODUCTS_FROM_EXCLUDED_PRODUCTS_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)
    shipping_method = content["data"]["shippingPriceRemoveProductFromExclude"][
        "shippingMethod"
    ]
    excluded_products = shipping_method["excludedProducts"]
    total_count = excluded_products["totalCount"]
    expected_product_ids = {
        graphene.Node.to_global_id("Product", p.pk) for p in product_list
    }
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert total_count == len(expected_product_ids)
    assert excluded_product_ids == expected_product_ids


@freeze_time("2022-05-12 12:00:00")
@pytest.mark.parametrize("requestor", ["staff", "app"])
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_remove_products_from_excluded_products_for_shipping_method_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    requestor,
    any_webhook,
    shipping_method,
    product_list,
    staff_api_client,
    permission_manage_shipping,
    product,
    app_api_client,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    shipping_method.excluded_products.set(product_list)
    shipping_method.excluded_products.add(product)

    product_ids = [
        graphene.Node.to_global_id("Product", product.pk),
    ]
    variables = {"id": shipping_method_id, "products": product_ids}

    # when
    response = api.post_graphql(
        REMOVE_PRODUCTS_FROM_EXCLUDED_PRODUCTS_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    issuer = SimpleLazyObject(lambda: api.user if requestor == "staff" else api.app)

    # then
    assert content["data"]["shippingPriceRemoveProductFromExclude"]["shippingMethod"]
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
        allow_replica=False,
    )
