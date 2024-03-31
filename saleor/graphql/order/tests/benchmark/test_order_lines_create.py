from decimal import Decimal

import graphene
import pytest

from .....discount import RewardValueType
from .....order import OrderStatus
from .....product.models import (
    ProductVariant,
    ProductVariantChannelListing,
    VariantChannelListingPromotionRule,
)
from ....tests.utils import get_graphql_content

ORDER_LINES_CREATE_MUTATION = """
    mutation OrderLinesCreate(
            $orderId: ID!,
            $input: [OrderLineCreateInput!]!
        ) {
        orderLinesCreate(
            id: $orderId,
            input: $input
        ) {
            errors {
                field
                code
                message
                variants
            }
            orderLines {
                id
            }
        }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_order_lines_create(
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    product_list,
    count_queries,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    line_input = [
        {
            "quantity": quantity,
            "variantId": graphene.Node.to_global_id("ProductVariant", variant.id),
        }
        for variant in ProductVariant.objects.all()
    ]
    variables = {"orderId": order_id, "input": line_input}

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert not data["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_order_lines_create_variants_on_promotion(
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    product_list,
    count_queries,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    reward_value = Decimal("10.00")
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "productPredicate": {
                "ids": [
                    graphene.Node.to_global_id("Product", product.id)
                    for product in product_list
                ]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=reward_value,
    )

    variant_ids = [variant.id for variant in ProductVariant.objects.all()]
    channel_listings = ProductVariantChannelListing.objects.filter(
        variant__in=variant_ids, channel=order.channel
    )

    VariantChannelListingPromotionRule.objects.bulk_create(
        [
            VariantChannelListingPromotionRule(
                variant_channel_listing=channel_listing,
                promotion_rule=rule,
                discount_amount=Decimal("1.00"),
                currency=order.currency,
            )
            for channel_listing in channel_listings
        ]
    )

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    line_input = [
        {
            "quantity": quantity,
            "variantId": graphene.Node.to_global_id("ProductVariant", variant_id),
        }
        for variant_id in variant_ids
    ]
    variables = {"orderId": order_id, "input": line_input}

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert not data["errors"]
