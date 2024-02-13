import graphene
import pytest

from .....discount import PromotionEvents
from .....discount.models import PromotionEvent
from .....product.models import ProductChannelListing
from ....tests.utils import assert_no_permission, get_graphql_content
from ...utils import get_products_for_promotion

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


def test_promotion_rule_delete_by_staff_user(
    staff_api_client,
    permission_group_manage_discounts,
    catalogue_promotion,
    product,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion.rules.get(name="Percentage promotion rule")
    variables = {"id": graphene.Node.to_global_id("PromotionRule", rule.id)}
    channels_ids = set(rule.channels.values_list("id", flat=True))
    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleDelete"]
    assert data["promotionRule"]["name"] == rule.name
    with pytest.raises(rule._meta.model.DoesNotExist):
        rule.refresh_from_db()

    listings = ProductChannelListing.objects.filter(
        channel__in=channels_ids, product=product
    )
    for listing in listings:
        assert listing.discounted_price_dirty is True


def test_promotion_rule_delete_by_staff_app(
    app_api_client,
    permission_manage_discounts,
    catalogue_promotion,
    product,
):
    # given
    promotion = catalogue_promotion
    rule = promotion.rules.get(name="Percentage promotion rule")
    variables = {"id": graphene.Node.to_global_id("PromotionRule", rule.id)}
    channels_ids = set(rule.channels.values_list("id", flat=True))

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

    listings = ProductChannelListing.objects.filter(
        channel__in=channels_ids, product=product
    )
    for listing in listings:
        assert listing.discounted_price_dirty is True


def test_promotion_rule_delete_by_customer(api_client, catalogue_promotion):
    # given
    promotion = catalogue_promotion
    rule = promotion.rules.first()
    variables = {"id": graphene.Node.to_global_id("PromotionRule", rule.id)}
    products = get_products_for_promotion(promotion)
    channels_ids = set(rule.channels.values_list("id", flat=True))

    # when
    response = api_client.post_graphql(PROMOTION_RULE_DELETE_MUTATION, variables)

    # then
    assert_no_permission(response)
    listings = ProductChannelListing.objects.filter(
        channel__in=channels_ids, product__in=products
    )
    for listing in listings:
        assert listing.discounted_price_dirty is False


def test_promotion_delete_clears_old_sale_id(
    staff_api_client,
    permission_group_manage_discounts,
    promotion_converted_from_sale,
    product,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion = promotion_converted_from_sale
    rule = promotion.rules.first()
    channels_ids = set(rule.channels.values_list("id", flat=True))

    assert promotion.old_sale_id

    variables = {"id": graphene.Node.to_global_id("PromotionRule", rule.id)}

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_DELETE_MUTATION, variables)

    # then
    listings = ProductChannelListing.objects.filter(
        channel__in=channels_ids, product=product
    )
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleDelete"]
    assert data["promotionRule"]["name"] == rule.name
    with pytest.raises(rule._meta.model.DoesNotExist):
        rule.refresh_from_db()

    promotion.refresh_from_db()
    assert promotion.old_sale_id is None

    for listing in listings:
        assert listing.discounted_price_dirty is True


def test_promotion_rule_delete_events(
    staff_api_client, permission_group_manage_discounts, catalogue_promotion
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = catalogue_promotion.rules.first()
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
