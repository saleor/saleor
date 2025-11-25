import pytest

from .....app.models import AppExtension
from ....tests.utils import get_graphql_content

QUERY_APP_EXTENSIONS = """
query ($filter: AppExtensionFilterInput){
    appExtensions(first: 10, filter: $filter){
    edges{
      node{
        label
        url
        mount
        target
        mountName
        targetName
        id
      }
    }
  }
}
"""


# Behavior specific to 3.22 which handles backwards compatibility
@pytest.mark.parametrize(
    ("mount_value", "target_value", "filter", "expected_count"),
    [
        # Test with uppercase values in database, lowercase input
        (
            "ORDER_DETAILS_WIDGETS",
            "WIDGET",
            {"mountName": ["order_details_widgets"]},
            1,
        ),
        ("ORDER_DETAILS_WIDGETS", "WIDGET", {"targetName": "widget"}, 1),
        (
            "ORDER_DETAILS_WIDGETS",
            "WIDGET",
            {"mountName": ["order_details_widgets"], "targetName": "widget"},
            1,
        ),
        # Test with uppercase values in database, uppercase input
        (
            "ORDER_DETAILS_WIDGETS",
            "WIDGET",
            {"mountName": ["ORDER_DETAILS_WIDGETS"]},
            1,
        ),
        ("ORDER_DETAILS_WIDGETS", "WIDGET", {"targetName": "WIDGET"}, 1),
        (
            "ORDER_DETAILS_WIDGETS",
            "WIDGET",
            {"mountName": ["ORDER_DETAILS_WIDGETS"], "targetName": "WIDGET"},
            1,
        ),
        # Test with lowercase values in database, uppercase input
        (
            "order_details_widgets",
            "widget",
            {"mountName": ["ORDER_DETAILS_WIDGETS"]},
            1,
        ),
        ("order_details_widgets", "widget", {"targetName": "WIDGET"}, 1),
        (
            "order_details_widgets",
            "widget",
            {"mountName": ["ORDER_DETAILS_WIDGETS"], "targetName": "WIDGET"},
            1,
        ),
        # Test with lowercase values in database, lowercase input
        (
            "order_details_widgets",
            "widget",
            {"mountName": ["order_details_widgets"]},
            1,
        ),
        ("order_details_widgets", "widget", {"targetName": "widget"}, 1),
        (
            "order_details_widgets",
            "widget",
            {"mountName": ["order_details_widgets"], "targetName": "widget"},
            1,
        ),
        # Test mixed case input
        (
            "ORDER_DETAILS_WIDGETS",
            "WIDGET",
            {"mountName": ["Order_Details_Widgets"]},
            1,
        ),
        ("ORDER_DETAILS_WIDGETS", "WIDGET", {"targetName": "WiDgEt"}, 1),
    ],
)
def test_app_extensions_case_insensitive_filter(
    mount_value,
    target_value,
    filter,
    expected_count,
    staff_api_client,
    app,
):
    # given
    AppExtension.objects.create(
        app=app,
        label="Test Extension",
        url="https://www.example.com/app-extension",
        mount=mount_value,
        target=target_value,
    )
    variables = {"filter": filter}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSIONS,
        variables,
    )

    # then
    content = get_graphql_content(response)
    extensions_data = content["data"]["appExtensions"]["edges"]

    assert len(extensions_data) == expected_count
