import graphene
import pytest

from ....discount import DiscountValueType, VoucherType
from ....discount.models import Voucher, VoucherChannelListing
from ...tests.utils import assert_graphql_error_with_message, get_graphql_content


@pytest.fixture
def vouchers_for_sorting_with_channels(db, channel_USD, channel_PLN):
    vouchers = Voucher.objects.bulk_create(
        [
            Voucher(
                code="Code1",
                name="Voucher1",
                discount_value_type=DiscountValueType.PERCENTAGE,
                usage_limit=10,
                type=VoucherType.SPECIFIC_PRODUCT,
            ),
            Voucher(
                code="Code2",
                name="Voucher2",
                usage_limit=1000,
                used=10,
                type=VoucherType.ENTIRE_ORDER,
            ),
            Voucher(
                code="Code3",
                name="Voucher3",
                discount_value_type=DiscountValueType.PERCENTAGE,
                usage_limit=100,
                used=35,
                type=VoucherType.ENTIRE_ORDER,
            ),
            Voucher(
                code="Code4",
                name="Voucher4",
                usage_limit=100,
                type=VoucherType.SPECIFIC_PRODUCT,
            ),
            Voucher(
                code="Code15",
                name="Voucher15",
                discount_value_type=DiscountValueType.PERCENTAGE,
                usage_limit=10,
            ),
        ]
    )
    VoucherChannelListing.objects.bulk_create(
        [
            VoucherChannelListing(
                voucher=vouchers[0],
                channel=channel_USD,
                discount_value=1,
                min_spent_amount=10,
                currency=channel_USD.currency_code,
            ),
            VoucherChannelListing(
                voucher=vouchers[1],
                channel=channel_USD,
                discount_value=7,
                currency=channel_USD.currency_code,
            ),
            VoucherChannelListing(
                voucher=vouchers[2],
                channel=channel_USD,
                discount_value=5,
                min_spent_amount=12,
                currency=channel_USD.currency_code,
            ),
            VoucherChannelListing(
                voucher=vouchers[4],
                channel=channel_USD,
                discount_value=2,
                min_spent_amount=100,
                currency=channel_USD.currency_code,
            ),
            # Second channel
            VoucherChannelListing(
                voucher=vouchers[0],
                channel=channel_PLN,
                discount_value=7,
                min_spent_amount=10,
                currency=channel_PLN.currency_code,
            ),
            VoucherChannelListing(
                voucher=vouchers[1],
                channel=channel_PLN,
                discount_value=1,
                min_spent_amount=100,
                currency=channel_PLN.currency_code,
            ),
            VoucherChannelListing(
                voucher=vouchers[3],
                channel=channel_PLN,
                discount_value=2,
                min_spent_amount=50,
                currency=channel_PLN.currency_code,
            ),
            VoucherChannelListing(
                voucher=vouchers[4],
                channel=channel_PLN,
                discount_value=5,
                currency=channel_PLN.currency_code,
            ),
        ]
    )
    return vouchers


QUERY_VOUCHERS_WITH_SORTING_AND_FILTERING = """
    query (
        $sortBy: VoucherSortingInput, $filter: VoucherFilterInput, $channel: String
    ){
        vouchers(
            first: 10, sortBy: $sortBy, filter: $filter, channel: $channel
        ) {
            edges {
                node {
                    name
                    id
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "sort_by",
    [
        {"field": "MINIMUM_SPENT_AMOUNT", "direction": "ASC"},
        {"field": "VALUE", "direction": "ASC"},
    ],
)
def test_voucher_with_sorting_and_without_channel(
    sort_by,
    staff_api_client,
    permission_manage_discounts,
):
    # given
    variables = {"sortBy": sort_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHERS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    assert_graphql_error_with_message(response, "A default channel does not exist.")


@pytest.mark.parametrize(
    "sort_by, vouchers_order",
    [
        (
            {"field": "VALUE", "direction": "ASC"},
            ["Voucher1", "Voucher15", "Voucher3", "Voucher2"],
        ),
        (
            {"field": "VALUE", "direction": "DESC"},
            ["Voucher2", "Voucher3", "Voucher15", "Voucher1"],
        ),
        (
            {"field": "MINIMUM_SPENT_AMOUNT", "direction": "ASC"},
            ["Voucher1", "Voucher3", "Voucher15", "Voucher2"],
        ),
        (
            {"field": "MINIMUM_SPENT_AMOUNT", "direction": "DESC"},
            ["Voucher2", "Voucher15", "Voucher3", "Voucher1"],
        ),
    ],
)
def test_vouchers_with_sorting_and_channel_USD(
    sort_by,
    vouchers_order,
    staff_api_client,
    permission_manage_discounts,
    vouchers_for_sorting_with_channels,
    channel_USD,
):
    # given
    variables = {"sortBy": sort_by, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHERS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    vouchers_nodes = content["data"]["vouchers"]["edges"]
    for index, voucher_name in enumerate(vouchers_order):
        assert voucher_name == vouchers_nodes[index]["node"]["name"]


@pytest.mark.parametrize(
    "sort_by, vouchers_order",
    [
        (
            {"field": "VALUE", "direction": "ASC"},
            ["Voucher2", "Voucher4", "Voucher15", "Voucher1"],
        ),
        (
            {"field": "VALUE", "direction": "DESC"},
            ["Voucher1", "Voucher15", "Voucher4", "Voucher2"],
        ),
        (
            {"field": "MINIMUM_SPENT_AMOUNT", "direction": "ASC"},
            ["Voucher1", "Voucher4", "Voucher2", "Voucher15"],
        ),
        (
            {"field": "MINIMUM_SPENT_AMOUNT", "direction": "DESC"},
            ["Voucher15", "Voucher2", "Voucher4", "Voucher1"],
        ),
    ],
)
def test_vouchers_with_sorting_and_channel_PLN(
    sort_by,
    vouchers_order,
    staff_api_client,
    permission_manage_discounts,
    vouchers_for_sorting_with_channels,
    channel_PLN,
):
    # given
    variables = {"sortBy": sort_by, "channel": channel_PLN.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHERS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    vouchers_nodes = content["data"]["vouchers"]["edges"]
    for index, voucher_name in enumerate(vouchers_order):
        assert voucher_name == vouchers_nodes[index]["node"]["name"]


@pytest.mark.parametrize(
    "sort_by",
    [
        {"field": "VALUE", "direction": "ASC"},
        {"field": "MINIMUM_SPENT_AMOUNT", "direction": "ASC"},
    ],
)
def test_vouchers_with_sorting_and_not_existing_channel_asc(
    sort_by,
    staff_api_client,
    permission_manage_discounts,
    vouchers_for_sorting_with_channels,
    channel_USD,
):
    # given
    variables = {"sortBy": sort_by, "channel": "Not-existing"}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHERS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["vouchers"]["edges"]


@pytest.mark.parametrize(
    "filter_by, vouchers_count",
    [
        ({"status": "ACTIVE"}, 4),
        ({"status": "SCHEDULED"}, 0),
        ({"status": "EXPIRED"}, 0),
        ({"timesUsed": {"gte": 11}}, 1),
        ({"timesUsed": {"lte": 1}}, 2),
        ({"discountType": "PERCENTAGE"}, 3),
        ({"discountType": "FIXED"}, 1),
        ({"discountType": "SHIPPING"}, 0),
        ({"search": "Code"}, 4),
    ],
)
def test_vouchers_with_filter_and_channel_USD(
    filter_by,
    vouchers_count,
    staff_api_client,
    permission_manage_discounts,
    vouchers_for_sorting_with_channels,
    channel_USD,
):
    # given
    variables = {"filter": filter_by, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHERS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    vouchers_nodes = content["data"]["vouchers"]["edges"]
    assert len(vouchers_nodes) == vouchers_count


def test_vouchers_with_filter_by_ids_and_channel_USD(
    staff_api_client,
    permission_manage_discounts,
    vouchers_for_sorting_with_channels,
    channel_USD,
):
    # given
    vouchers = [
        vouchers_for_sorting_with_channels[0],
        vouchers_for_sorting_with_channels[1],
    ]
    ids = [graphene.Node.to_global_id("Voucher", voucher.id) for voucher in vouchers]
    variables = {"filter": {"ids": ids}, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHERS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    vouchers_nodes = content["data"]["vouchers"]["edges"]
    assert len(vouchers_nodes) == len(vouchers)
    for voucher in vouchers_nodes:
        assert voucher["node"]["id"] in ids
