import pytest

from .....core.telemetry import Scope, Unit
from .....tests.utils import get_metric_data
from ....api import backend, schema
from ....metrics import METRIC_GRAPHQL_ALIAS_COUNT
from ....views import GraphQLView


@pytest.mark.parametrize(
    ("_case", "is_valid", "query"),
    [
        ("Alias count lower than limit should be allowed", True, "{x:__typename}"),
        (
            "Too many aliases -> should reject",
            False,
            "{x1: __typename, x2: __typename, x3: __typename}",
        ),
        (
            "Aliases should be counted even if query is nested",
            False,
            """
            {
                alias1: products(first: 10) {
                    alias2: edges {
                        node {
                            alias3: id
                        }
                    }
                }
            }
            """,
        ),
        (
            "Should count both mutations and response queries",
            False,
            """
            {
                mutation {
                    alias1: tokenCreate(email:"x", password:"x"){ token }
                    alias2: tokenCreate(email:"x", password:"x"){ token }
                    tokenCreate(email:"x", password:"x"){ query: token }
                }
            }
            """,
        ),
        (
            "Should count even if using multiple operations",
            False,
            """
            query a {
                alias1: tokenCreate(email: "x", password: "x") { __typename }
            }
            query b {
                alias2: tokenCreate(email: "x", password: "x") { __typename }
            }
            query b {
                alias3: tokenCreate(email: "x", password: "x") { __typename }
            }
            """,
        ),
    ],
)
def test_limits_number_of_aliases(
    api_client, settings, _case: str, is_valid: bool, query: str
):
    # Prevent mutation limiter from triggering as we want to test alias validation
    settings.GRAPHQL_MUTATION_COUNT_LIMIT = 10
    settings.GRAPHQL_ALIAS_COUNT_LIMIT = 2

    # When sending a batch with only 1 query, it should allow it
    resp = api_client.post(data={"query": query})
    resp_data = resp.json()
    resp_data.pop("extensions")

    if is_valid:
        assert resp_data == {"data": {"x": "Query"}}
        assert resp.status_code == 200
    else:
        assert resp_data == {
            "errors": [
                {
                    "extensions": {"exception": {"code": "GraphQLError"}},
                    "message": "Number of aliases exceed the limit of 2",
                }
            ]
        }
        assert resp.status_code == 400


@pytest.mark.parametrize(
    ("query", "expected_count"),
    [
        (
            """
                {
                    alias1: __typename
                    alias2: __typename
                    alias3: __typename
                }
        """,
            3,
        ),
        (
            # Sending too many aliases should cause the metric to not be recorded
            """
                {
                    alias1: __typename
                    alias2: __typename
                    alias3: __typename
                    alias4: __typename
                }
            """,
            None,
        ),
        # Shouldn't measure queries without any aliases
        ("{__typename}", None),
    ],
)
def test_metric_recorded(
    get_test_metrics_data, rf, settings, query: str, expected_count: int | None
):
    settings.GRAPHQL_ALIAS_COUNT_LIMIT = 3

    # Send the request
    data = {"query": query}
    request = rf.post(path="/graphql/", data=data, content_type="application/json")
    GraphQLView.as_view(backend=backend, schema=schema)(request)

    # Check the metric
    metrics_data = get_test_metrics_data()
    metric = get_metric_data(metrics_data, METRIC_GRAPHQL_ALIAS_COUNT, scope=Scope.CORE)

    if expected_count is None:
        assert metric is None, "shouldn't have recorded the metric"
    else:
        assert metric is not None, "should have found a metric"
        data_point = metric.data.data_points[0]
        assert metric.unit == Unit.COUNT.value
        assert data_point.attributes == {}
        assert data_point.max == expected_count
