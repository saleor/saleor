from unittest.mock import patch

import graphene
import pytest

from .....discount import PromotionEvents
from .....discount.models import PromotionEvent
from ....tests.utils import assert_no_permission, get_graphql_content

PROMOTION_RULE_DELETE_MUTATION = """
    mutation promotionRuleDelete($id: ID!) {
        promotionRuleDelete(id: $id) {
            promotionRule {
                name
                id
                promotion {
                    events {
                        ... on PromotionEventInterface {
                            type
                        }
                        ... on PromotionRuleEventInterface {
                            ruleId
                        }
                    }
                }
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.promotion_rule_deleted")
@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_promotion_rule_delete_by_staff_user(
    update_products_discounted_prices_for_promotion_task_mock,
    promotion_rule_deleted_mock,
    staff_api_client,
    permission_group_manage_discounts,
    promotion,
    product,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion.rules.get(name="Percentage promotion rule")
    variables = {"id": graphene.Node.to_global_id("PromotionRule", rule.id)}

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleDelete"]
    assert data["promotionRule"]["name"] == rule.name
    with pytest.raises(rule._meta.model.DoesNotExist):
        rule.refresh_from_db()

    update_products_discounted_prices_for_promotion_task_mock.assert_called_once_with(
        [product.id]
    )
    promotion_rule_deleted_mock.assert_called_once_with(rule)


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_promotion_rule_delete_by_staff_app(
    update_products_discounted_prices_for_promotion_task_mock,
    app_api_client,
    permission_manage_discounts,
    promotion,
    product,
):
    # given
    rule = promotion.rules.get(name="Percentage promotion rule")
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

    update_products_discounted_prices_for_promotion_task_mock.assert_called_once_with(
        [product.id]
    )


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_promotion_rule_delete_by_customer(
    update_products_discounted_prices_for_promotion_task_mock, api_client, promotion
):
    # given
    rule = promotion.rules.first()
    variables = {"id": graphene.Node.to_global_id("PromotionRule", rule.id)}

    # when
    response = api_client.post_graphql(PROMOTION_RULE_DELETE_MUTATION, variables)

    # then
    assert_no_permission(response)
    update_products_discounted_prices_for_promotion_task_mock.assert_not_called()


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_promotion_delete_clears_old_sale_id(
    update_products_discounted_prices_for_promotion_task_mock,
    staff_api_client,
    permission_group_manage_discounts,
    promotion_converted_from_sale,
    product,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion = promotion_converted_from_sale
    rule = promotion.rules.first()

    assert promotion.old_sale_id

    variables = {"id": graphene.Node.to_global_id("PromotionRule", rule.id)}

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleDelete"]
    assert data["promotionRule"]["name"] == rule.name
    with pytest.raises(rule._meta.model.DoesNotExist):
        rule.refresh_from_db()

    update_products_discounted_prices_for_promotion_task_mock.assert_called_once_with(
        [product.id]
    )

    promotion.refresh_from_db()
    assert promotion.old_sale_id is None


def test_promotion_rule_delete_events(
    staff_api_client, permission_group_manage_discounts, promotion
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)
    variables = {"id": rule_id}
    event_count = PromotionEvent.objects.count()

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleDelete"]
    assert not data["errors"]

    events = data["promotionRule"]["promotion"]["events"]
    assert len(events) == 1
    assert PromotionEvent.objects.count() == event_count + 1
    assert PromotionEvents.RULE_DELETED.upper() == events[0]["type"]

    assert events[0]["ruleId"] == rule_id
