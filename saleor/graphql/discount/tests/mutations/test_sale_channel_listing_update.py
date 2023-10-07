from unittest.mock import patch

import graphene
import pytest

from .....discount import DiscountValueType
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion, PromotionRule, SaleChannelListing
from ....tests.utils import assert_negative_positive_decimal_value, get_graphql_content

SALE_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateSaleChannelListing(
    $id: ID!
    $input: SaleChannelListingInput!
) {
    saleChannelListingUpdate(id: $id, input: $input) {
        errors {
            field
            message
            code
            channels
        }
        sale {
            name
            channelListings {
                discountValue
                channel {
                    slug
                }
            }
        }
    }
}
"""


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_sale_task"
)
def test_sale_channel_listing_create_as_staff_user(
    mock_update_discounted_prices_of_discount_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_PLN,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    discounted = 1.12

    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discounted}]
        },
    }

    # when

    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["saleChannelListingUpdate"]
    shipping_method_data = data["sale"]
    assert not data["errors"]
    assert shipping_method_data["name"] == sale.name

    assert shipping_method_data["channelListings"][1]["discountValue"] == discounted
    assert (
        shipping_method_data["channelListings"][1]["channel"]["slug"]
        == channel_PLN.slug
    )
    mock_update_discounted_prices_of_discount_task.delay.assert_called_once_with(
        sale.pk,
    )


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_sale_task"
)
def test_sale_channel_listing_updates_rule_listings(
    mock_update_discounted_prices_of_discount_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_PLN,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    discounted = 1.12

    sale_listing = sale.channel_listings.first()
    product = sale.products.first()

    promotion = Promotion.objects.create(name="Test", old_sale_id=sale.pk)
    rule = promotion.rules.create(
        reward_value_type=sale.type,
        reward_value=sale_listing.discount_value,
        catalogue_predicate={
            "OR": [
                {
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.pk)]
                    }
                }
            ]
        },
    )
    rule.channels.add(channel_USD)
    variant = product.variants.first()
    variant_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    rule_listing = variant_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=sale_listing.discount_value,
        currency=channel_USD.currency_code,
    )

    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discounted}],
            "removeChannels": [graphene.Node.to_global_id("Channel", channel_USD.id)],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["saleChannelListingUpdate"]
    sale_data = data["sale"]
    assert not data["errors"]
    assert sale_data["name"] == sale.name

    assert len(sale_data["channelListings"]) == 1
    assert sale_data["channelListings"][0]["discountValue"] == discounted
    assert sale_data["channelListings"][0]["channel"]["slug"] == channel_PLN.slug
    with pytest.raises(rule._meta.model.DoesNotExist):
        rule.refresh_from_db()
    assert promotion.rules.count() == 1
    new_rule = promotion.rules.first()
    assert new_rule.channels.count() == 1
    assert new_rule.channels.first() == channel_PLN

    with pytest.raises(rule_listing._meta.model.DoesNotExist):
        rule_listing.refresh_from_db()

    mock_update_discounted_prices_of_discount_task.delay.assert_called_once_with(
        sale.pk,
    )


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_sale_task"
)
def test_sale_channel_listing_creates_promotion_and_rule_listings(
    mock_update_discounted_prices_of_discount_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_PLN,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    discounted = 1.12

    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discounted}],
            "removeChannels": [graphene.Node.to_global_id("Channel", channel_USD.id)],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["saleChannelListingUpdate"]
    sale_data = data["sale"]
    assert not data["errors"]
    assert sale_data["name"] == sale.name

    assert len(sale_data["channelListings"]) == 1
    assert sale_data["channelListings"][0]["discountValue"] == discounted
    assert sale_data["channelListings"][0]["channel"]["slug"] == channel_PLN.slug
    mock_update_discounted_prices_of_discount_task.delay.assert_called_once_with(
        sale.pk,
    )

    promotion = Promotion.objects.get(old_sale_id=sale.pk)
    assert promotion.rules.count() == 2
    channel_ids = PromotionRule.channels.through.objects.values_list(
        "channel_id", flat=True
    )
    assert list(channel_ids) == [channel_PLN.id]


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_sale_task"
)
def test_sale_channel_listing_update_as_staff_user(
    mock_update_discounted_prices_of_discount_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted = 10.11

    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discounted}]
        },
    }
    channel_listing = SaleChannelListing.objects.get(
        sale_id=sale.pk, channel_id=channel_USD.id
    )
    assert channel_listing.discount_value == 5

    # when

    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["saleChannelListingUpdate"]
    shipping_method_data = data["sale"]
    assert not data["errors"]

    assert shipping_method_data["channelListings"][0]["discountValue"] == discounted
    mock_update_discounted_prices_of_discount_task.delay.assert_called_once_with(
        sale.pk,
    )


def test_sale_channel_listing_update_with_negative_discounted_value(
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted_value = -10

    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [
                {"channelId": channel_id, "discountValue": discounted_value}
            ]
        },
    }
    channel_listing = SaleChannelListing.objects.get(
        sale_id=sale.pk, channel_id=channel_USD.id
    )
    assert channel_listing.discount_value == 5

    # when
    staff_api_client.user.user_permissions.add(permission_manage_discounts)

    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
    )
    assert_negative_positive_decimal_value(response)


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_sale_task"
)
def test_sale_channel_listing_update_duplicated_ids_in_add_and_remove(
    mock_update_discounted_prices_of_discount_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted = 10.11
    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discounted}],
            "removeChannels": [channel_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["saleChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == DiscountErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]
    mock_update_discounted_prices_of_discount_task.assert_not_called()


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_sale_task"
)
def test_sale_channel_listing_update_duplicated_channel_in_add(
    mock_update_discounted_prices_of_discount_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted = 10.11
    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [
                {"channelId": channel_id, "discountValue": discounted},
                {"channelId": channel_id, "discountValue": discounted},
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["saleChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "addChannels"
    assert errors[0]["code"] == DiscountErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]
    mock_update_discounted_prices_of_discount_task.assert_not_called()


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_sale_task"
)
def test_sale_channel_listing_update_duplicated_channel_in_remove(
    mock_update_discounted_prices_of_discount_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": sale_id,
        "input": {"removeChannels": [channel_id, channel_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["saleChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "removeChannels"
    assert errors[0]["code"] == DiscountErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]
    mock_update_discounted_prices_of_discount_task.assert_not_called()


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_sale_task"
)
def test_sale_channel_listing_update_with_invalid_decimal_places(
    mock_update_discounted_prices_of_discount_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    discounted = 1.123
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discounted}],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)
    # then
    errors = content["data"]["saleChannelListingUpdate"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors[0]["field"] == "input"
    assert errors[0]["channels"] == [channel_id]
    mock_update_discounted_prices_of_discount_task.assert_not_called()


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_sale_task"
)
def test_sale_channel_listing_update_with_invalid_percentage_value(
    mock_update_discounted_prices_of_discount_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale = sale
    sale.type = DiscountValueType.PERCENTAGE
    sale.save()
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    discounted = 101
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discounted}],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)
    # then
    errors = content["data"]["saleChannelListingUpdate"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors[0]["field"] == "input"
    assert errors[0]["channels"] == [channel_id]
    mock_update_discounted_prices_of_discount_task.assert_not_called()


SALE_AND_SALE_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateSaleChannelListing(
    $id: ID!
    $saleInput: SaleInput!
    $channelInput: SaleChannelListingInput!
) {
    saleUpdate(id: $id, input: $saleInput) {
        errors {
            code
        }
        sale {
            channelListings {
                id
            }
        }
    }
    saleChannelListingUpdate(id: $id, input: $channelInput) {
        errors {
            code
        }
        sale {
            channelListings {
                id
                channel {
                    id
                }
            }
        }
    }
}
"""


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_sale_task"
)
def test_invalidate_data_sale_channel_listings_update(
    mock_update_discounted_prices_of_discount_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    discount_value = 10
    sale.channel_listings.all().delete()
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": sale_id,
        "saleInput": {},
        "channelInput": {
            "addChannels": [{"channelId": channel_id, "discountValue": discount_value}],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_AND_SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    channel_listing = sale.channel_listings.first()
    assert channel_listing.discount_value == discount_value
    assert channel_listing.channel_id == channel_USD.id

    sale_errors = content["data"]["saleUpdate"]["errors"]
    channel_listings_errors = content["data"]["saleChannelListingUpdate"]["errors"]
    assert not sale_errors
    assert not channel_listings_errors

    sale_data = content["data"]["saleUpdate"]["sale"]
    channel_listings_data = content["data"]["saleChannelListingUpdate"]["sale"]

    # response from the first mutation is empty
    assert sale_data["channelListings"] == []

    # response from the second mutation contains data
    assert channel_listings_data["channelListings"][0]["channel"]["id"] == channel_id
    mock_update_discounted_prices_of_discount_task.delay.assert_called_once_with(
        sale.pk,
    )
