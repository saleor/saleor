import gc
import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder

from ....api import backend, schema
from ....tests.utils import get_graphql_content
from ....views import GraphQLView
from .utils import (
    clean_up_after_garbage_collection_test,
    disable_gc_for_garbage_collection_test,
)

PRODUCTS_QUERY = """
query FetchProducts($first: Int, $channel: String!){
    products(first: $first, channel: $channel) {
        edges {
            node {
                id
                name
                defaultVariant {
                    name
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
def test_query_remove_all_memory_cycles_in_promise(rf, product, channel_USD):
    try:
        # given
        # Disable automatic garbage collection and set debugging flag.
        disable_gc_for_garbage_collection_test()
        # Prepare request body with GraphQL query and variables.
        variables = {"channel": channel_USD.slug, "first": 1}
        data = {"query": PRODUCTS_QUERY, "variables": variables}
        data = json.dumps(data, cls=DjangoJSONEncoder)

        # when
        # Execute the query.
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
        # Ensure that the query returned the expected data.
        assert content["data"]["products"]["edges"][0]["node"]["name"] == product.name
    # Restore garbage collection settings to their original state. This should always be run to avoid interfering
    # with other tests to ensure that code should be executed in the `finally' block.
    finally:
        clean_up_after_garbage_collection_test()
