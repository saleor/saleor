import gc
import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder

from .....core.jwt import create_access_token
from ....api import backend, schema
from ....tests.utils import get_graphql_content
from ....views import GraphQLView
from .utils import (
    clean_up_after_garbage_collection_test,
    disable_gc_for_garbage_collection_test,
)

PRODUCTS_QUERY = """
{
    me {
        email
    }
}
"""


# Group all tests that require garbage collection so that they do not run concurrently.
# This is necessary to ensure that tests don't interfere with each other.
# Without grouping we could receive false positive results.
@pytest.mark.xdist_group(name="garbage_collection")
def test_query_remove_SaleorContext_memory_cycles(rf, staff_user):
    try:
        # given
        # Disable automatic garbage collection and set debugging flag.
        disable_gc_for_garbage_collection_test()
        # Prepare request body with GraphQL query.
        data = {"query": PRODUCTS_QUERY}
        data = json.dumps(data, cls=DjangoJSONEncoder)
        jwt_token = create_access_token(staff_user)

        # when
        # Execute the query as staff user.
        content = get_graphql_content(
            GraphQLView(backend=backend, schema=schema).handle_query(
                rf.post(
                    path="/graphql/",
                    data=data,
                    content_type="application/json",
                    headers={"authorization": f"JWT {jwt_token}"},
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
        # Ensure that the query returned the expected data.
        assert content["data"]["me"]["email"] == staff_user.email
    # Restore garbage collection settings to their original state. This should always be run to avoid interfering
    # with other tests to ensure that code should be executed in the `finally' block.
    finally:
        clean_up_after_garbage_collection_test()
