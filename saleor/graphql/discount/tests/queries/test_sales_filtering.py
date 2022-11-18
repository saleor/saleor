from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....discount import DiscountValueType
from .....discount.models import Sale, SaleChannelListing
from ....tests.utils import get_graphql_content

QUERY_SALES_WITH_FILTER = """
    query ($filter: SaleFilterInput!, ) {
      sales(first:5, filter: $filter){
        edges{
          node{
            id
            name
            startDate
          }
        }
      }
    }
"""


@pytest.mark.parametrize(
    "sale_filter, start_date, end_date, count",
    [
        (
            {"status": "ACTIVE"},
            timezone.now().replace(year=2015, month=1, day=1),
            timezone.now() + timedelta(days=365),
            2,
        ),
        (
            {"status": "EXPIRED"},
            timezone.now().replace(year=2015, month=1, day=1),
            timezone.now().replace(year=2018, month=1, day=1),
            1,
        ),
        (
            {"status": "SCHEDULED"},
            timezone.now() + timedelta(days=3),
            timezone.now() + timedelta(days=10),
            1,
        ),
    ],
)
def test_query_sales_with_filter_status(
    sale_filter,
    start_date,
    end_date,
    count,
    staff_api_client,
    permission_manage_discounts,
    channel_USD,
):
    sales = Sale.objects.bulk_create(
        [
            Sale(name="Sale1", start_date=timezone.now()),
            Sale(name="Sale2", start_date=start_date, end_date=end_date),
        ]
    )
    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(
                sale=sale,
                discount_value=123,
                channel=channel_USD,
                currency=channel_USD.currency_code,
            )
            for sale in sales
        ]
    )

    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_FILTER, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "sale_filter, count, sale_type",
    [
        ({"saleType": "PERCENTAGE"}, 1, DiscountValueType.PERCENTAGE),
        ({"saleType": "FIXED"}, 2, DiscountValueType.FIXED),
    ],
)
def test_query_sales_with_filter_discount_type(
    sale_filter,
    count,
    sale_type,
    staff_api_client,
    permission_manage_discounts,
):
    Sale.objects.bulk_create(
        [
            Sale(name="Sale1", type=DiscountValueType.FIXED),
            Sale(name="Sale2", type=sale_type),
        ]
    )
    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_FILTER, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "sale_filter, count",
    [
        ({"started": {"gte": "2019-04-18T00:00:00+00:00"}}, 1),
        ({"started": {"lte": "2012-01-14T00:00:00+00:00"}}, 1),
        (
            {
                "started": {
                    "lte": "2012-01-15T00:00:00+00:00",
                    "gte": "2012-01-01T00:00:00+00:00",
                }
            },
            1,
        ),
        ({"started": {"gte": "2012-01-03T00:00:00+00:00"}}, 2),
    ],
)
def test_query_sales_with_filter_started(
    sale_filter,
    count,
    staff_api_client,
    permission_manage_discounts,
    channel_USD,
):
    sales = Sale.objects.bulk_create(
        [
            Sale(name="Sale1"),
            Sale(
                name="Sale2",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
        ]
    )
    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(
                sale=sale,
                discount_value=123,
                channel=channel_USD,
                currency=channel_USD.currency_code,
            )
            for sale in sales
        ]
    )

    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_FILTER, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "sale_filter, count",
    [
        ({"updatedAt": {"gte": "2012-01-14T10:59:00+00:00"}}, 2),
        ({"updatedAt": {"lte": "2012-01-14T12:00:05+00:00"}}, 2),
        ({"updatedAt": {"gte": "2012-01-14T11:59:00+00:00"}}, 1),
        ({"updatedAt": {"lte": "2012-01-14T11:05:00+00:00"}}, 1),
        ({"updatedAt": {"gte": "2012-01-14T12:01:00+00:00"}}, 0),
        ({"updatedAt": {"lte": "2012-01-14T10:59:00+00:00"}}, 0),
        (
            {
                "updatedAt": {
                    "lte": "2012-01-14T12:01:00+00:00",
                    "gte": "2012-01-14T11:59:00+00:00",
                },
            },
            1,
        ),
    ],
)
def test_query_sales_with_filter_updated_at(
    sale_filter,
    count,
    staff_api_client,
    permission_manage_discounts,
    channel_USD,
):
    with freeze_time("2012-01-14 11:00:00"):
        sale_1 = Sale.objects.create(name="Sale1")

    with freeze_time("2012-01-14 12:00:00"):
        sale_2 = Sale.objects.create(name="Sale2")

    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(
                sale=sale,
                discount_value=123,
                channel=channel_USD,
                currency=channel_USD.currency_code,
            )
            for sale in [sale_1, sale_2]
        ]
    )

    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_FILTER, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "sale_filter, count",
    [({"search": "Big"}, 1), ({"search": "69"}, 1), ({"search": "FIX"}, 2)],
)
def test_query_sales_with_filter_search(
    sale_filter,
    count,
    staff_api_client,
    permission_manage_discounts,
    channel_USD,
):
    sales = Sale.objects.bulk_create(
        [
            Sale(name="BigSale", type="PERCENTAGE"),
            Sale(
                name="Sale2",
                type="FIXED",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
            Sale(
                name="Sale3",
                type="FIXED",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
        ]
    )
    values = [123, 123, 69]
    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(channel=channel_USD, discount_value=values[i], sale=sale)
            for i, sale in enumerate(sales)
        ]
    )
    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_FILTER, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count
