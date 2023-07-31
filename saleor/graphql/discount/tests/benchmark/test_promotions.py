from decimal import Decimal

import graphene
import pytest

from .....discount import RewardValueType
from .....discount.models import (
    Promotion,
    PromotionRule,
    PromotionRuleTranslation,
    PromotionTranslation,
)
from ....tests.utils import get_graphql_content


@pytest.fixture
def promotion_list(channel_USD, channel_PLN, product_list):
    promotions = Promotion.objects.bulk_create(
        [Promotion(name=f"Promotion-{i}") for i in range(30)]
    )
    rules = [
        PromotionRule(
            promotion=promotion,
            catalogue_predicate={},
            reward_value_type=RewardValueType.PERCENTAGE,
            reward_value=Decimal("10"),
        )
        for promotion in promotions
    ]
    for rule, product in zip(rules, product_list):
        rule.catalogue_predicate = {
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product.id)]
            }
        }

    PromotionRule.objects.bulk_create(rules)

    channel_PLN.promotionrule_set.add(*rules)
    channel_USD.promotionrule_set.add(*rules)

    # TODO: add translations
    promotion_translations = []
    for promotion in promotions:
        promotion_translations.append(
            PromotionTranslation(
                language_code="pl",
                promotion=promotion,
                name="Polish promotion name",
            )
        )
    PromotionTranslation.objects.bulk_create(promotion_translations)

    promotion_rule_translations = []
    for rule in rules:
        promotion_rule_translations.append(
            PromotionRuleTranslation(
                language_code="pl",
                promotion_rule=rule,
                name="Polish promotion rule name",
            )
        )
    PromotionRuleTranslation.objects.bulk_create(promotion_rule_translations)

    return promotions


PROMOTIONS_QUERY = """
query {
    promotions(first: 10) {
        edges {
            node {
                id
                name
                description
                startDate
                endDate
                createdAt
                updatedAt
                rules {
                    id
                    name
                    description
                    channels {
                        id
                        slug
                    }
                    rewardValueType
                    rewardValue
                    cataloguePredicate
                    translation(languageCode: PL) {
                        name
                    }
                }
                translation(languageCode: PL) {
                    name
                }
            }
        }
    }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_promotions_querytest_promotions_query(
    staff_api_client,
    promotion_list,
    permission_group_manage_discounts,
    count_queries,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_discounts)

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            PROMOTIONS_QUERY,
            {},
        )
    )

    # then
    data = content["data"]["promotions"]
    assert data
