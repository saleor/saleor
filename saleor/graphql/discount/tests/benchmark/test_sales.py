import pytest

from .....discount import RewardValueType
from .....discount.models import Promotion, PromotionRule
from ....tests.utils import get_graphql_content


@pytest.fixture
def promotion_converted_from_sale_list(channel_USD, channel_PLN):
    promotions = Promotion.objects.bulk_create(
        [Promotion(name="Sale1"), Promotion(name="Sale2"), Promotion(name="Sale2")]
    )
    for promotion in promotions:
        promotion.assign_old_sale_id()

    values = [15, 5, 25]
    usd_rules, pln_rules = [], []
    for promotion, value in zip(promotions, values):
        usd_rules.append(
            PromotionRule(
                promotion=promotion,
                catalogue_predicate={},
                reward_value_type=RewardValueType.FIXED,
                reward_value=value,
            )
        )
        pln_rules.append(
            PromotionRule(
                promotion=promotion,
                catalogue_predicate={},
                reward_value_type=RewardValueType.FIXED,
                reward_value=value * 2,
            )
        )
    PromotionRule.objects.bulk_create(usd_rules + pln_rules)
    PromotionRuleChannel = PromotionRule.channels.through
    usd_rules_channels = [
        PromotionRuleChannel(promotionrule_id=rule.id, channel_id=channel_USD.id)
        for rule in usd_rules
    ]
    pln_rules_channels = [
        PromotionRuleChannel(promotionrule_id=rule.id, channel_id=channel_PLN.id)
        for rule in usd_rules
    ]
    PromotionRuleChannel.objects.bulk_create(usd_rules_channels + pln_rules_channels)

    return promotions


SALES_QUERY = """
query GetSales($channel: String){
  sales(last: 10, channel: $channel) {
    edges {
      node {
        id
        name
        type
        startDate
        endDate
        categories(first: 10) {
          edges {
            node {
              id
            }
          }
        }
        collections(first: 10) {
          edges {
            node {
              id
            }
          }
        }
        products(first: 10) {
          edges {
            node {
              id
            }
          }
        }
        variants(first: 10) {
          edges {
            node {
              id
            }
          }
        }
        channelListings {
          id
          discountValue
          currency
          channel {
            id
            name
            isActive
            slug
            currencyCode
          }
        }
        discountValue
        currency
      }
    }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_sales_query_with_channel_slug(
    staff_api_client,
    promotion_converted_from_sale_list,
    channel_USD,
    permission_manage_discounts,
    count_queries,
):
    variables = {"channel": channel_USD.slug}
    get_graphql_content(
        staff_api_client.post_graphql(
            SALES_QUERY,
            variables,
            permissions=[permission_manage_discounts],
            check_no_permissions=False,
        )
    )


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_sales_query_without_channel_slug(
    staff_api_client,
    promotion_converted_from_sale_list,
    permission_manage_discounts,
    count_queries,
):
    get_graphql_content(
        staff_api_client.post_graphql(
            SALES_QUERY,
            {},
            permissions=[permission_manage_discounts],
            check_no_permissions=False,
        )
    )
