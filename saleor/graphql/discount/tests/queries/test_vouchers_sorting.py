import graphene
import pytest
from django.utils import timezone

from .....discount import DiscountValueType, VoucherType
from .....discount.models import Voucher, VoucherChannelListing, VoucherCode
from ....tests.utils import assert_graphql_error_with_message, get_graphql_content


@pytest.fixture
def vouchers_for_sorting_with_channels(db, channel_USD, channel_PLN):
    vouchers = Voucher.objects.bulk_create(
        [
            Voucher(
                name="Voucher1",
                discount_value_type=DiscountValueType.PERCENTAGE,
                type=VoucherType.SPECIFIC_PRODUCT,
                usage_limit=10,
            ),
            Voucher(name="Voucher2", type=VoucherType.ENTIRE_ORDER, usage_limit=1000),
            Voucher(
                name="Voucher3",
                discount_value_type=DiscountValueType.PERCENTAGE,
                type=VoucherType.ENTIRE_ORDER,
                usage_limit=100,
            ),
            Voucher(
                name="Voucher4",
                type=VoucherType.SPECIFIC_PRODUCT,
                usage_limit=100,
            ),
            Voucher(
                name="Voucher15",
                discount_value_type=DiscountValueType.PERCENTAGE,
                usage_limit=10,
            ),
        ]
    )

    VoucherCode.objects.bulk_create(
        [
            VoucherCode(code="Code1", voucher=vouchers[0]),
            VoucherCode(code="Code2", used=10, voucher=vouchers[1]),
            VoucherCode(code="Code3", used=35, voucher=vouchers[2]),
            VoucherCode(code="Code4", voucher=vouchers[3]),
            VoucherCode(code="Code15", voucher=vouchers[4]),
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
    ("sort_by", "vouchers_order"),
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
    ("sort_by", "vouchers_order"),
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
    ("filter_by", "vouchers_count"),
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


QUERY_VOUCHER_WITH_SORT = """
    query ($sort_by: VoucherSortingInput!) {
        vouchers(first:5, sortBy: $sort_by) {
            edges{
                node{
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    ("voucher_sort", "result_order"),
    [
        (
            {"field": "CODE", "direction": "ASC"},
            [
                "Voucher2",
                "Voucher1",
                "FreeShipping",
            ],
        ),
        (
            {"field": "CODE", "direction": "DESC"},
            ["FreeShipping", "Voucher1", "Voucher2"],
        ),
        (
            {"field": "TYPE", "direction": "ASC"},
            ["Voucher1", "Voucher2", "FreeShipping"],
        ),
        (
            {"field": "TYPE", "direction": "DESC"},
            ["FreeShipping", "Voucher2", "Voucher1"],
        ),
        (
            {"field": "START_DATE", "direction": "ASC"},
            ["FreeShipping", "Voucher2", "Voucher1"],
        ),
        (
            {"field": "START_DATE", "direction": "DESC"},
            ["Voucher1", "Voucher2", "FreeShipping"],
        ),
        (
            {"field": "END_DATE", "direction": "ASC"},
            ["Voucher2", "FreeShipping", "Voucher1"],
        ),
        (
            {"field": "END_DATE", "direction": "DESC"},
            ["Voucher1", "FreeShipping", "Voucher2"],
        ),
        (
            {"field": "USAGE_LIMIT", "direction": "ASC"},
            ["Voucher1", "FreeShipping", "Voucher2"],
        ),
        (
            {"field": "USAGE_LIMIT", "direction": "DESC"},
            ["Voucher2", "FreeShipping", "Voucher1"],
        ),
    ],
)
def test_query_vouchers_with_sort(
    voucher_sort, result_order, staff_api_client, permission_manage_discounts
):
    vouchers = Voucher.objects.bulk_create(
        [
            Voucher(
                name="Voucher1",
                discount_value_type=DiscountValueType.FIXED,
                type=VoucherType.ENTIRE_ORDER,
                usage_limit=10,
            ),
            Voucher(
                name="Voucher2",
                discount_value_type=DiscountValueType.FIXED,
                type=VoucherType.ENTIRE_ORDER,
                start_date=timezone.now().replace(year=2012, month=1, day=5),
                end_date=timezone.now().replace(year=2013, month=1, day=5),
            ),
            Voucher(
                name="FreeShipping",
                discount_value_type=DiscountValueType.PERCENTAGE,
                type=VoucherType.SHIPPING,
                start_date=timezone.now().replace(year=2011, month=1, day=5),
                end_date=timezone.now().replace(year=2015, month=12, day=31),
                usage_limit=1000,
            ),
        ]
    )

    VoucherCode.objects.bulk_create(
        [
            VoucherCode(code="abc", voucher=vouchers[0]),
            VoucherCode(code="123", voucher=vouchers[1]),
            VoucherCode(code="xyz", voucher=vouchers[2]),
        ]
    )
    variables = {"sort_by": voucher_sort}
    staff_api_client.user.user_permissions.add(permission_manage_discounts)
    response = staff_api_client.post_graphql(QUERY_VOUCHER_WITH_SORT, variables)
    content = get_graphql_content(response)
    vouchers = content["data"]["vouchers"]["edges"]

    for order, voucher_name in enumerate(result_order):
        assert vouchers[order]["node"]["name"] == voucher_name
