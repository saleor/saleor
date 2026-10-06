import graphene
from django.db import connection
from django.test.utils import CaptureQueriesContext

from .....attribute.models import AttributeValue
from .....discount.models import PromotionRuleCustomerAttributeValue
from ....tests.utils import get_graphql_content

QUERY_PROMOTION_RULES_BUYER_CONDITIONS = """
    query Promotion($id: ID!) {
        promotion(id: $id) {
            rules {
                id
                customerTypes {
                    id
                    name
                }
                customerAttributeValues {
                    id
                    name
                }
            }
        }
    }
"""

CONDITION_TABLES = (
    '"discount_promotionrulecustomertype"',
    '"discount_promotionrulecustomerattributevalue"',
)


def test_promotion_rules_expose_their_buyer_conditions(
    staff_api_client,
    permission_group_manage_discounts,
    promotion_rule_for_customer_type,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion_rule_for_customer_type
    gold_value = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="gold"
    )
    PromotionRuleCustomerAttributeValue.objects.create(rule=rule, value=gold_value)
    promotion = rule.promotion
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.pk)}

    # when
    with CaptureQueriesContext(connection) as context:
        response = staff_api_client.post_graphql(
            QUERY_PROMOTION_RULES_BUYER_CONDITIONS, variables
        )

    # then
    rules_data = get_graphql_content(response)["data"]["promotion"]["rules"]
    assert len(rules_data) == promotion.rules.count()
    rule_data = next(
        data
        for data in rules_data
        if data["id"] == graphene.Node.to_global_id("PromotionRule", rule.pk)
    )
    assert rule_data["customerTypes"] == [
        {
            "id": graphene.Node.to_global_id("CustomerType", customer_type.pk),
            "name": customer_type.name,
        }
    ]
    assert rule_data["customerAttributeValues"] == [
        {
            "id": graphene.Node.to_global_id("AttributeValue", gold_value.pk),
            "name": gold_value.name,
        }
    ]
    for data in rules_data:
        if data is not rule_data:
            assert data["customerTypes"] == []
            assert data["customerAttributeValues"] == []
    for table in CONDITION_TABLES:
        condition_queries = [
            query for query in context.captured_queries if table in query["sql"]
        ]
        assert len(condition_queries) == 1
