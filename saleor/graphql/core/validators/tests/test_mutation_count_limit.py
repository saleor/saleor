import pytest

from .....core.telemetry import Scope, Unit
from .....tests.utils import get_metric_data
from ....api import backend, schema
from ....metrics import METRIC_GRAPHQL_MUTATION_COUNT
from ....views import GraphQLView


@pytest.mark.parametrize(
    ("_case", "is_valid", "query"),
    [
        (
            "Mutation count lower than the limit should be allowed",
            True,
            """
            mutation {
                tokenCreate(email: "x", password: "x") { __typename }
            }
            """,
        ),
        (
            "Too many mutations -> should reject",
            False,
            """
            mutation {
                tokenCreate(email: "x", password: "x") { __typename }
                tokenVerify(token: "x") { __typename }
                tokenRefresh(refreshToken: "x") { __typename }
            }
            """,
        ),
        (
            "Mutations should be counted even when using aliases",
            False,
            """
            mutation {
                tokenCreate(email: "x", password: "x") { __typename }
                alias: tokenCreate(email: "x", password: "x") { __typename }
                alias2: tokenCreate(email: "x", password: "x") { __typename }
            }
            """,
        ),
        (
            "Should count even if using multiple operations",
            False,
            """
            mutation {
                tokenCreate(email: "x", password: "x") { __typename }
            }
            mutation {
                tokenCreate(email: "x", password: "x") { __typename }
            }
            mutation {
                tokenCreate(email: "x", password: "x") { __typename }
            }
            """,
        ),
    ],
)
def test_limits_number_of_aliases(
    api_client, settings, _case: str, is_valid: bool, query: str
):
    # Prevent alias limiter from triggering as we want to test alias validation
    settings.GRAPHQL_ALIAS_COUNT_LIMIT = 10
    settings.GRAPHQL_MUTATION_COUNT_LIMIT = 2

    # When sending a batch with only 1 query, it should allow it
    resp = api_client.post(data={"query": query})
    resp_data = resp.json()
    resp_data.pop("extensions")

    if is_valid:
        assert "errors" not in resp_data
        assert resp.status_code == 200
    else:
        assert resp_data == {
            "errors": [
                {
                    "extensions": {"exception": {"code": "GraphQLError"}},
                    "message": "Number of mutations exceed the limit of 2",
                }
            ]
        }
        assert resp.status_code == 400


@pytest.mark.parametrize(
    ("query", "expected_count"),
    [
        (
            # Sends 2 mutations
            """
                mutation {
                    productUpdate(input: {name: "my-product"}, id: "UHJvZHVjdDox") {
                        __typename
                    }
                    collectionUpdate(input: {name: "my-collection"}, id: "Q29sbGVjdGlvbjoy") {
                        __typename
                    }
                }
        """,
            2,
        ),
        (
            # Sends 1 mutations. We expect it to not be recorded as 1 mutation
            # per API request is a typical use.
            """
                mutation {
                    tokenCreate(email: "x", password: "x") { __typename}
                }
        """,
            None,
        ),
        (
            # Sends 3 mutations which is too many.
            # Ensures users sending too many mutations aren't counted
            """
                mutation {
                    mutation1: tokenCreate(email: "x", password: "x")
                    mutation2: tokenCreate(email: "x", password: "x")
                    mutation3: tokenCreate(email: "x", password: "x")
                }
            """,
            None,
        ),
    ],
)
def test_metric_recorded(
    get_test_metrics_data, rf, settings, query: str, expected_count: int | None
):
    """Should record the number of mutations sent."""

    settings.GRAPHQL_ALIAS_COUNT_LIMIT = 10
    settings.GRAPHQL_MUTATION_COUNT_LIMIT = 2

    # Send the request
    data = {"query": query}
    request = rf.post(path="/graphql/", data=data, content_type="application/json")
    GraphQLView.as_view(backend=backend, schema=schema)(request)

    # Check the metric
    metrics_data = get_test_metrics_data()
    metric = get_metric_data(
        metrics_data, METRIC_GRAPHQL_MUTATION_COUNT, scope=Scope.CORE
    )

    if expected_count is None:
        assert metric is None, "shouldn't have recorded the metric"
    else:
        assert metric is not None, "should have found a metric"
        data_point = metric.data.data_points[0]
        assert metric.unit == Unit.COUNT.value
        assert data_point.attributes == {}
        assert data_point.max == expected_count
