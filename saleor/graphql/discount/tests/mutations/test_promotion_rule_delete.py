import graphene
import pytest

from ....tests.utils import assert_no_permission, get_graphql_content

PROMOTION_RULE_DELETE_MUTATION = """
    mutation promotionRuleDelete($id: ID!) {
        promotionRuleDelete(id: $id) {
            promotionRule {
                name
                id
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_promotion_delete_by_staff_user(
    staff_api_client, permission_group_manage_discounts, promotion
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion.rules.first()
    variables = {"id": graphene.Node.to_global_id("PromotionRule", rule.id)}

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleDelete"]
    assert data["promotionRule"]["name"] == rule.name
    with pytest.raises(rule._meta.model.DoesNotExist):
        rule.refresh_from_db()


def test_promotion_delete_by_staff_app(
    app_api_client, permission_manage_discounts, promotion
):
    # given
    rule = promotion.rules.first()
    variables = {"id": graphene.Node.to_global_id("PromotionRule", rule.id)}

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_DELETE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleDelete"]
    assert data["promotionRule"]["name"] == rule.name
    with pytest.raises(rule._meta.model.DoesNotExist):
        rule.refresh_from_db()


def test_promotion_delete_by_customer(api_client, promotion):
    # given
    rule = promotion.rules.first()
    variables = {"id": graphene.Node.to_global_id("PromotionRule", rule.id)}

    # when
    response = api_client.post_graphql(PROMOTION_RULE_DELETE_MUTATION, variables)

    # then
    assert_no_permission(response)
