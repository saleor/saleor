from datetime import timedelta

import pytest
from django.utils import timezone

from .....discount import RewardValueType
from .....discount.models import Promotion, PromotionRule
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
    ("sale_filter", "start_date", "end_date", "count"),
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
    # given
    promotions = Promotion.objects.bulk_create(
        [
            Promotion(name="Sale1", start_date=timezone.now()),
            Promotion(name="Sale2", start_date=start_date, end_date=end_date),
        ]
    )
    for promotion in promotions:
        promotion.assign_old_sale_id()

    variables = {"filter": sale_filter}

    # when
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_FILTER, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    ("sale_filter", "count", "sale_type"),
    [
        ({"saleType": "PERCENTAGE"}, 1, RewardValueType.PERCENTAGE),
        ({"saleType": "FIXED"}, 2, RewardValueType.FIXED),
    ],
)
def test_query_sales_with_filter_discount_type(
    sale_filter,
    count,
    sale_type,
    staff_api_client,
    permission_manage_discounts,
):
    # given
    promotions = Promotion.objects.bulk_create(
        [
            Promotion(name="Sale1"),
            Promotion(name="Sale2"),
        ]
    )
    for promotion in promotions:
        promotion.assign_old_sale_id()
    PromotionRule.objects.create(
        promotion=promotions[0],
        reward_value=123,
        reward_value_type=RewardValueType.FIXED,
    )
    PromotionRule.objects.create(
        promotion=promotions[1],
        reward_value=123,
        reward_value_type=sale_type,
    )

    variables = {"filter": sale_filter}

    # when
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_FILTER, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    ("sale_filter", "count"),
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
    # given
    promotions = Promotion.objects.bulk_create(
        [
            Promotion(name="Sale1"),
            Promotion(
                name="Sale2",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
        ]
    )
    for promotion in promotions:
        promotion.assign_old_sale_id()

    variables = {"filter": sale_filter}

    # when
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_FILTER, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    ("sale_filter", "count"),
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
    # given
    promotions = Promotion.objects.bulk_create(
        [
            Promotion(name="Sale1"),
            Promotion(name="Sale2"),
        ]
    )
    for promotion in promotions:
        promotion.assign_old_sale_id()

    assert len(promotions) == 2
    promotions[0].updated_at = timezone.now().replace(
        year=2012, month=1, day=14, hour=11, minute=0, second=0
    )
    promotions[1].updated_at = timezone.now().replace(
        year=2012, month=1, day=14, hour=12, minute=0, second=0
    )
    Promotion.objects.bulk_update(promotions, ["updated_at"])

    variables = {"filter": sale_filter}

    # when
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_FILTER, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    ("sale_filter", "count"),
    [({"search": "Big"}, 1), ({"search": "69"}, 1), ({"search": "FIX"}, 2)],
)
def test_query_sales_with_filter_search(
    sale_filter,
    count,
    staff_api_client,
    permission_manage_discounts,
    channel_USD,
):
    # given
    promotions = Promotion.objects.bulk_create(
        [
            Promotion(name="BigSale"),
            Promotion(
                name="Sale2",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
            Promotion(
                name="Sale3",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
        ]
    )
    for promotion in promotions:
        promotion.assign_old_sale_id()

    values = [123, 123, 69]
    types = [RewardValueType.PERCENTAGE, RewardValueType.FIXED, RewardValueType.FIXED]

    PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                promotion=promotion,
                reward_value=values[i],
                reward_value_type=types[i],
            )
            for i, promotion in enumerate(promotions)
        ]
    )

    variables = {"filter": sale_filter}

    # when
    response = staff_api_client.post_graphql(
        QUERY_SALES_WITH_FILTER, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count
