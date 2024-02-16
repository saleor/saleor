from decimal import Decimal
from unittest import mock

import graphene
import pytest

from .....discount import RewardValueType
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion, PromotionRule
from .....product.models import ProductChannelListing, ProductVariant
from ....tests.utils import get_graphql_content


@pytest.fixture
def promotion_converted_from_sale_list(channel_USD, product_list, category, collection):
    promotions = Promotion.objects.bulk_create(
        [Promotion(name="Sale 1"), Promotion(name="Sale 2"), Promotion(name="Sale 3")]
    )
    for promotion in promotions:
        promotion.assign_old_sale_id()
    predicates = [
        {
            "OR": [
                {
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                {
                    "variantPredicate": {
                        "ids": [
                            graphene.Node.to_global_id(
                                "Product", product.variants.first().id
                            )
                        ]
                    }
                },
            ]
        }
        for product in product_list
    ]
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)

    predicates[0]["OR"].append({"categoryPredicate": {"ids": [category_id]}})
    predicates[1]["OR"].append({"collectionPredicate": {"ids": [collection_id]}})

    rules = [
        PromotionRule(
            promotion=promotion,
            catalogue_predicate=predicate,
            reward_value_type=RewardValueType.FIXED,
            reward_value=Decimal("5"),
        )
        for promotion, predicate in zip(promotions, predicates)
    ]
    PromotionRule.objects.bulk_create(rules)
    for rule in rules:
        rule.channels.add(channel_USD)

    return promotions


SALE_BULK_DELETE_MUTATION = """
    mutation saleBulkDelete($ids: [ID!]!) {
        saleBulkDelete(ids: $ids) {
            count
            errors {
                field
                code
            }
        }
    }
    """


@mock.patch("saleor.graphql.discount.mutations.bulk_mutations.get_webhooks_for_event")
@mock.patch("saleor.plugins.manager.PluginsManager.sale_deleted")
def test_delete_sales(
    deleted_webhook_mock,
    mocked_get_webhooks_for_event,
    staff_api_client,
    promotion_converted_from_sale_list,
    permission_manage_discounts,
    any_webhook,
    settings,
):
    # given
    rules_to_delete = PromotionRule.objects.filter(
        promotion_id__in=[
            promotion.id for promotion in promotion_converted_from_sale_list
        ]
    )
    variant_ids = PromotionRule.variants.through.objects.filter(
        promotionrule_id__in=rules_to_delete
    ).values_list("productvariant_id", flat=True)
    product_ids = ProductVariant.objects.filter(id__in=variant_ids).values_list(
        "product_id", flat=True
    )

    promotion_list = promotion_converted_from_sale_list
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variables = {
        "ids": [
            graphene.Node.to_global_id("Sale", promotion.old_sale_id)
            for promotion in promotion_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_BULK_DELETE_MUTATION, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["saleBulkDelete"]["count"] == 3
    assert not Promotion.objects.filter(
        id__in=[promotion.id for promotion in promotion_list]
    ).exists()

    assert not ProductChannelListing.objects.filter(
        product_id__in=product_ids, discounted_price_dirty=False
    ).exists()

    assert deleted_webhook_mock.call_count == len(promotion_list)


@mock.patch("saleor.graphql.discount.mutations.bulk_mutations.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_sales_triggers_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    staff_api_client,
    promotion_converted_from_sale_list,
    permission_manage_discounts,
    any_webhook,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    promotion_list = promotion_converted_from_sale_list

    variables = {
        "ids": [
            graphene.Node.to_global_id("Sale", promotion.old_sale_id)
            for promotion in promotion_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_BULK_DELETE_MUTATION, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["saleBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.call_count == 3


@mock.patch("saleor.graphql.discount.mutations.bulk_mutations.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_sales_with_variants_triggers_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    staff_api_client,
    promotion_converted_from_sale_list,
    permission_manage_discounts,
    any_webhook,
    settings,
    product,
    collection,
    category,
    product_variant_list,
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    product_id = graphene.Node.to_global_id("Product", product.id)
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]
    predicate = {
        "OR": [
            {"collectionPredicate": {"ids": [collection_id]}},
            {"categoryPredicate": {"ids": [category_id]}},
            {"productPredicate": {"ids": [product_id]}},
            {"variantPredicate": {"ids": variant_ids}},
        ]
    }

    promotion_list = promotion_converted_from_sale_list
    rules = [promotion.rules.first() for promotion in promotion_list]
    for rule in rules:
        rule.catalogue_predicate = predicate

    PromotionRule.objects.bulk_update(rules, fields=["catalogue_predicate"])

    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variables = {
        "ids": [
            graphene.Node.to_global_id("Sale", promotion.old_sale_id)
            for promotion in promotion_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_BULK_DELETE_MUTATION, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["saleBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.call_count == 3


@mock.patch("saleor.graphql.discount.mutations.bulk_mutations.get_webhooks_for_event")
@mock.patch("saleor.plugins.manager.PluginsManager.sale_deleted")
def test_delete_sales_with_promotion_ids(
    deleted_webhook_mock,
    mocked_get_webhooks_for_event,
    staff_api_client,
    any_webhook,
    promotion_converted_from_sale_list,
    permission_manage_discounts,
    settings,
):
    # given
    rules_to_delete = PromotionRule.objects.filter(
        promotion_id__in=[
            promotion.id for promotion in promotion_converted_from_sale_list
        ]
    )
    variant_ids = PromotionRule.variants.through.objects.filter(
        promotionrule_id__in=rules_to_delete
    ).values_list("productvariant_id", flat=True)
    product_ids = ProductVariant.objects.filter(id__in=variant_ids).values_list(
        "product_id", flat=True
    )

    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variables = {
        "ids": [
            graphene.Node.to_global_id("Promotion", promotion.id)
            for promotion in promotion_converted_from_sale_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_BULK_DELETE_MUTATION, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)

    assert not content["data"]["saleBulkDelete"]["count"]
    errors = content["data"]["saleBulkDelete"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name

    deleted_webhook_mock.assert_not_called()
    assert not ProductChannelListing.objects.filter(
        product_id__in=product_ids, discounted_price_dirty=True
    ).exists()
