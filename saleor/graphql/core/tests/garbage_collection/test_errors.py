import gc
import json
from unittest import mock

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.test import override_settings
from graphql.error import GraphQLError

from ....api import backend, schema
from ....tests.utils import get_graphql_content
from ....views import GraphQLView
from .utils import (
    clean_up_after_garbage_collection_test,
    disable_gc_for_garbage_collection_test,
)


def raise_graphql_error(*args, **kwargs):
    raise GraphQLError("Exception in resolver")


PRODUCTS_QUERY_PERMISSION_REQUIRED = """
query FetchProducts($channel: String!){
    products(first: 10, channel: $channel) {
        edges {
            node {
                id
                name
                channelListings{
                  id
                }
            }
        }
    }
}
"""


# Group all tests that require garbage collection so that they do not run concurrently.
# This is necessary to ensure that tests don't interfere with each other.
# Without grouping we could receive false positive results.
@pytest.mark.xdist_group(name="garbage_collection")
def test_permission_error(rf, product, channel_USD):
    try:
        # given
        # Disable automatic garbage collection and set debugging flag.
        disable_gc_for_garbage_collection_test()
        # Prepare request body with GraphQL query and variables.
        variables = {"channel": channel_USD.slug}
        data = {"query": PRODUCTS_QUERY_PERMISSION_REQUIRED, "variables": variables}
        data = json.dumps(data, cls=DjangoJSONEncoder)

        # when
        # Execute the query with permission error.
        content = get_graphql_content(
            GraphQLView(backend=backend, schema=schema).handle_query(
                rf.post(path="/graphql/", data=data, content_type="application/json")
            ),
            ignore_errors=True,
        )
        # Enforce garbage collection to populate the garbage list for inspection.
        gc.collect()

        # then
        # Ensure that the garbage list is empty. The garbage list is only valid
        # until the next collection cycle so we can only make assertions about it
        # before re-enabling automatic collection.
        assert gc.garbage == []
        # Ensure that the query returned the expected error.
        assert content["data"]["products"]["edges"][0]["node"]["name"] == product.name
        assert (
            content["errors"][0]["extensions"]["exception"]["code"]
            == "PermissionDenied"
        )
    # Restore garbage collection settings to their original state. This should always be run to avoid interfering
    # with other tests to ensure that code should be executed in the `finally' block.
    finally:
        clean_up_after_garbage_collection_test()


PRODUCTS_QUERY = """
query FetchProducts($first: Int, $channel: String!){
    products(first: $first, channel: $channel) {
        edges {
            node {
                id
                name
                variants {
                    id
                }
            }
        }
    }
}
"""


# Group all tests that require garbage collection so that they do not run concurrently.
# This is necessary to ensure that tests don't interfere with each other.
# Without grouping we could receive false positive results.
@pytest.mark.xdist_group(name="garbage_collection")
@override_settings(GRAPHQL_QUERY_MAX_COMPLEXITY=5)
def test_query_cost_error(rf, product, channel_USD):
    try:
        # given
        # Disable automatic garbage collection and set debugging flag.
        disable_gc_for_garbage_collection_test()
        # Prepare request body with GraphQL query and variables.
        variables = {"channel": channel_USD.slug, "first": 10}
        data = {"query": PRODUCTS_QUERY, "variables": variables}
        data = json.dumps(data, cls=DjangoJSONEncoder)

        # when
        # Execute the query with cost error.
        content = get_graphql_content(
            GraphQLView(backend=backend, schema=schema).handle_query(
                rf.post(path="/graphql/", data=data, content_type="application/json")
            ),
            ignore_errors=True,
        )
        # Enforce garbage collection to populate the garbage list for inspection.
        gc.collect()

        # then
        # Ensure that the garbage list is empty. The garbage list is only valid
        # until the next collection cycle so we can only make assertions about it
        # before re-enabling automatic collection.
        assert gc.garbage == []
        # Ensure that the query returned the expected error.
        assert (
            content["errors"][0]["extensions"]["exception"]["code"] == "QueryCostError"
        )
    # Restore garbage collection settings to their original state. This should always be run to avoid interfering
    # with other tests to ensure that code should be executed in the `finally' block.
    finally:
        clean_up_after_garbage_collection_test()


# Group all tests that require garbage collection so that they do not run concurrently.
# This is necessary to ensure that tests don't interfere with each other.
# Without grouping we could receive false positive results.
@pytest.mark.xdist_group(name="garbage_collection")
def test_exception_in_resolver(rf, product, channel_USD):
    try:
        # given
        # Disable automatic garbage collection and set debugging flag.
        disable_gc_for_garbage_collection_test()
        # Prepare request body with GraphQL query and variables.
        variables = {"channel": channel_USD.slug, "first": 10}
        data = {"query": PRODUCTS_QUERY, "variables": variables}
        data = json.dumps(data, cls=DjangoJSONEncoder)

        # when
        # Execute the query with GraphQLError in the resolver.
        with mock.patch(
            "saleor.graphql.product.schema.resolve_products",
            side_effect=raise_graphql_error,
        ) as _mocked_resolver:
            content = get_graphql_content(
                GraphQLView(backend=backend, schema=schema).handle_query(
                    rf.post(
                        path="/graphql/", data=data, content_type="application/json"
                    )
                ),
                ignore_errors=True,
            )

        # Enforce garbage collection to populate the garbage list for inspection.
        gc.collect()

        # then
        # Ensure that the garbage list is empty. The garbage list is only valid
        # until the next collection cycle so we can only make assertions about it
        # before re-enabling automatic collection.
        assert gc.garbage == []
        # Ensure that the query returned the expected error.
        assert content["errors"][0]["extensions"]["exception"]["code"] == "GraphQLError"
    # Restore garbage collection settings to their original state. This should always be run to avoid interfering
    # with other tests to ensure that code should be executed in the `finally' block.
    finally:
        clean_up_after_garbage_collection_test()


# Group all tests that require garbage collection so that they do not run concurrently.
# This is necessary to ensure that tests don't interfere with each other.
# Without grouping we could receive false positive results.
@pytest.mark.xdist_group(name="garbage_collection")
def test_exception_in_dataloader(rf, product, channel_USD):
    try:
        # given
        # Disable automatic garbage collection and set debugging flag.
        disable_gc_for_garbage_collection_test()
        # Prepare request body with GraphQL query and variables.
        variables = {"channel": channel_USD.slug, "first": 10}
        data = {"query": PRODUCTS_QUERY, "variables": variables}
        data = json.dumps(data, cls=DjangoJSONEncoder)

        # when
        # Execute the query with GraphQLError in the dataloader.
        with mock.patch(
            "saleor.graphql.product.schema.ChannelBySlugLoader.batch_load",
            side_effect=raise_graphql_error,
        ) as _mocked_dataloader:
            content = get_graphql_content(
                GraphQLView(backend=backend, schema=schema).handle_query(
                    rf.post(
                        path="/graphql/", data=data, content_type="application/json"
                    )
                ),
                ignore_errors=True,
            )
        # Enforce garbage collection to populate the garbage list for inspection.
        gc.collect()

        # then
        # Ensure that the garbage list is empty. The garbage list is only valid
        # until the next collection cycle so we can only make assertions about it
        # before re-enabling automatic collection.
        assert gc.garbage == []
        # Ensure that the query returned the expected error.
        assert content["errors"][0]["extensions"]["exception"]["code"] == "GraphQLError"
    # Restore garbage collection settings to their original state. This should always be run to avoid interfering
    # with other tests to ensure that code should be executed in the `finally' block.
    finally:
        clean_up_after_garbage_collection_test()


STOCK_UPDATE = """
mutation ProductVariantStocksUpdate($variantId: ID!, $stocks: [StockInput!]!){
    productVariantStocksUpdate(variantId: $variantId, stocks: $stocks){
        productVariant {
            quantityAvailable
            stocks {
                id
            }
        }
        errors {
            code
        }
    }
}
"""


# Group all tests that require garbage collection so that they do not run concurrently.
# This is necessary to ensure that tests don't interfere with each other.
# Without grouping we could receive false positive results.
@pytest.mark.xdist_group(name="garbage_collection")
def test_input_validation_error(rf, product, channel_USD):
    try:
        # given
        # Disable automatic garbage collection and set debugging flag.
        disable_gc_for_garbage_collection_test()
        # Prepare request body with GraphQL query and variables.
        variables = {
            "variantId": "",
            "stocks": [{"warehouse": "", "quantity": 99999999999}],
        }
        data = {"query": STOCK_UPDATE, "variables": variables}
        data = json.dumps(data, cls=DjangoJSONEncoder)

        # when
        # Execute the mutation with input validation error.
        content = get_graphql_content(
            GraphQLView(backend=backend, schema=schema).handle_query(
                rf.post(path="/graphql/", data=data, content_type="application/json")
            ),
            ignore_errors=True,
        )
        # Enforce garbage collection to populate the garbage list for inspection.
        gc.collect()

        # then
        # Ensure that the garbage list is empty. The garbage list is only valid
        # until the next collection cycle so we can only make assertions about it
        # before re-enabling automatic collection.
        assert gc.garbage == []
        # Ensure that the query returned the expected error.
        assert content["errors"][0]["extensions"]["exception"]["code"] == "GraphQLError"
    # Restore garbage collection settings to their original state. This should always be run to avoid interfering
    # with other tests to ensure that code should be executed in the `finally' block.
    finally:
        clean_up_after_garbage_collection_test()
