import pytest

from ....discount import DiscountValueType
from ....discount.models import Sale, SaleChannelListing
from ...channel.sorters import LACK_OF_CHANNEL_IN_SORTING_MSG
from ...tests.utils import assert_graphql_error_with_message, get_graphql_content


@pytest.fixture
def sales_for_sorting_with_channels(db, channel_USD, channel_PLN):
    sales = Sale.objects.bulk_create(
        [
            Sale(
                name="Sale1",
                type=DiscountValueType.PERCENTAGE,
            ),
            Sale(name="Sale2"),
            Sale(
                name="Sale3",
                type=DiscountValueType.PERCENTAGE,
            ),
            Sale(name="Sale4"),
            Sale(name="Sale15"),
        ]
    )
    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(
                discount_value=1,
                sale=sales[0],
                channel=channel_USD,
                currency=channel_USD.currency_code,
            ),
            SaleChannelListing(
                discount_value=7,
                sale=sales[1],
                channel=channel_USD,
                currency=channel_USD.currency_code,
            ),
            SaleChannelListing(
                discount_value=5,
                sale=sales[2],
                channel=channel_USD,
                currency=channel_USD.currency_code,
            ),
            SaleChannelListing(
                discount_value=2,
                sale=sales[4],
                channel=channel_USD,
                currency=channel_USD.currency_code,
            ),
            # Second channel
            SaleChannelListing(
                discount_value=7,
                sale=sales[0],
                channel=channel_PLN,
                currency=channel_PLN.currency_code,
            ),
            SaleChannelListing(
                discount_value=1,
                sale=sales[1],
                channel=channel_PLN,
                currency=channel_PLN.currency_code,
            ),
            SaleChannelListing(
                discount_value=2,
                sale=sales[3],
                channel=channel_PLN,
                currency=channel_PLN.currency_code,
            ),
            SaleChannelListing(
                discount_value=5,
                sale=sales[4],
                channel=channel_PLN,
                currency=channel_PLN.currency_code,
            ),
        ]
    )
    return sales


QUERY_SALES_WITH_SORTING_AND_FILTERING = """
    query (
        $sortBy: SaleSortingInput, $filter: SaleFilterInput
    ){
        sales (
            first: 10, sortBy: $sortBy, filter: $filter
        ) {
            edges {
                node {
                    name
                }
            }
        }
    }
"""


def test_sales_with_sorting_and_without_channel(
    staff_api_client,
    permission_manage_discounts,
):
    # given
    variables = {"sortBy": {"field": "VALUE", "direction": "ASC"}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    assert_graphql_error_with_message(response, LACK_OF_CHANNEL_IN_SORTING_MSG)


@pytest.mark.parametrize(
    "sort_by, sales_order",
    [
        (
            {"field": "VALUE", "direction": "ASC"},
            ["Sale1", "Sale15", "Sale3", "Sale2", "Sale4"],
        ),
        (
            {"field": "VALUE", "direction": "DESC"},
            ["Sale4", "Sale2", "Sale3", "Sale15", "Sale1"],
        ),
    ],
)
def test_sales_with_sorting_and_channel_USD(
    sort_by,
    sales_order,
    staff_api_client,
    permission_manage_discounts,
    sales_for_sorting_with_channels,
    channel_USD,
):
    # given
    sort_by["channel"] = channel_USD.slug
    variables = {"sortBy": sort_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    sales_nodes = content["data"]["sales"]["edges"]
    for index, sale_name in enumerate(sales_order):
        assert sale_name == sales_nodes[index]["node"]["name"]


@pytest.mark.parametrize(
    "sort_by, sales_order",
    [
        (
            {"field": "VALUE", "direction": "ASC"},
            ["Sale2", "Sale4", "Sale15", "Sale1", "Sale3"],
        ),
        (
            {"field": "VALUE", "direction": "DESC"},
            ["Sale3", "Sale1", "Sale15", "Sale4", "Sale2"],
        ),
    ],
)
def test_sales_with_sorting_and_channel_PLN(
    sort_by,
    sales_order,
    staff_api_client,
    permission_manage_discounts,
    sales_for_sorting_with_channels,
    channel_PLN,
):
    # given
    sort_by["channel"] = channel_PLN.slug
    variables = {"sortBy": sort_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    sales_nodes = content["data"]["sales"]["edges"]
    for index, sale_name in enumerate(sales_order):
        assert sale_name == sales_nodes[index]["node"]["name"]


def test_vouchers_with_sorting_and_not_existing_channel_asc(
    staff_api_client,
    permission_manage_discounts,
    sales_for_sorting_with_channels,
    channel_USD,
):
    # given
    sales_order = [
        "Sale1",
        "Sale15",
        "Sale2",
        "Sale3",
        "Sale4",
    ]
    variables = {
        "sortBy": {"field": "VALUE", "direction": "ASC", "channel": "Not-existing"}
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    sales_nodes = content["data"]["sales"]["edges"]
    for index, sale_name in enumerate(sales_order):
        assert sale_name == sales_nodes[index]["node"]["name"]
