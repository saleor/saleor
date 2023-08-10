from unittest.mock import patch

import graphene

from .....discount import DiscountValueType
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion, PromotionRule, SaleChannelListing
from .....discount.sale_converter import (
    convert_sales_to_promotions,
    create_catalogue_predicate_from_sale,
)
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
    ".update_products_discounted_prices_of_promotion_task"
)
def test_sale_channel_listing_add_channels(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_PLN,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    discounted = 1.12

    channel_listing = SaleChannelListing.objects.filter(
        sale_id=sale.pk, channel_id=channel_PLN.id
    )
    assert len(channel_listing) == 0

    convert_sales_to_promotions()
    assert len(PromotionRule.objects.all()) == 1

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
    assert not content["data"]["saleChannelListingUpdate"]["errors"]
    data = content["data"]["saleChannelListingUpdate"]["sale"]
    assert data["name"] == sale.name

    channel_listing = data["channelListings"]
    discounts = [item["discountValue"] for item in channel_listing]
    slugs = [item["channel"]["slug"] for item in channel_listing]
    assert discounted in discounts
    assert channel_PLN.slug in slugs

    promotion = Promotion.objects.get(old_sale_id=sale.pk)
    rules = promotion.rules.all()
    assert len(rules) == 2
    assert (
        len({(rule.reward_value_type, str(rule.catalogue_predicate)) for rule in rules})
        == 1
    )
    assert all([rule.old_channel_listing_id for rule in rules])

    mock_update_products_discounted_prices_task.delay.assert_called_once_with(
        promotion.pk
    )


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_promotion_task"
)
def test_sale_channel_listing_update_channels(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted = 10.11
    convert_sales_to_promotions()

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
    assert not content["data"]["saleChannelListingUpdate"]["errors"]
    data = content["data"]["saleChannelListingUpdate"]["sale"]

    channel_listing = data["channelListings"]

    assert len(channel_listing) == 1
    assert channel_listing[0]["discountValue"] == discounted
    assert channel_listing[0]["channel"]["slug"] == channel_USD.slug

    promotion = Promotion.objects.get(old_sale_id=sale.pk)
    rules = promotion.rules.all()
    assert len(rules) == 1

    mock_update_products_discounted_prices_task.delay.assert_called_once_with(
        promotion.pk
    )


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_promotion_task"
)
def test_sale_channel_listing_remove_channels(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    sale_with_many_channels,
    permission_manage_discounts,
    channel_USD,
    channel_PLN,
):
    # given
    sale = sale_with_many_channels
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    channel_listing = SaleChannelListing.objects.filter(sale_id=sale.pk)
    assert len(channel_listing) == 2

    convert_sales_to_promotions()
    assert len(PromotionRule.objects.all()) == 2

    variables = {
        "id": sale_id,
        "input": {"removeChannels": [channel_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["saleChannelListingUpdate"]["errors"]
    data = content["data"]["saleChannelListingUpdate"]["sale"]
    assert data["name"] == sale.name

    channel_listing = data["channelListings"]
    assert len(channel_listing) == 1
    assert channel_listing[0]["channel"]["slug"] == channel_PLN.slug

    promotion = Promotion.objects.get(old_sale_id=sale.pk)
    rules = promotion.rules.all()
    assert len(rules) == 1

    mock_update_products_discounted_prices_task.delay.assert_called_once_with(
        promotion.pk
    )


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_promotion_task"
)
def test_sale_channel_listing_remove_all_channels(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    sale_with_many_channels,
    permission_manage_discounts,
    channel_USD,
    channel_PLN,
):
    # given
    sale = sale_with_many_channels
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.id)
        for channel in [channel_USD, channel_PLN]
    ]

    channel_listing = SaleChannelListing.objects.filter(sale_id=sale.pk)
    assert len(channel_listing) == 2

    convert_sales_to_promotions()
    assert len(PromotionRule.objects.all()) == 2

    variables = {
        "id": sale_id,
        "input": {"removeChannels": channel_ids},
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["saleChannelListingUpdate"]["errors"]
    data = content["data"]["saleChannelListingUpdate"]["sale"]
    assert data["name"] == sale.name
    assert not data["channelListings"]

    promotion = Promotion.objects.get(old_sale_id=sale.pk)
    # Despite removing the promotion from all channels, we ensure at least one rule
    # is assigned to promotion in order to determine old sale's type and catalogue
    rules = promotion.rules.all()
    assert len(rules) == 1
    assert rules[0].reward_value_type == sale.type
    assert rules[0].catalogue_predicate == create_catalogue_predicate_from_sale(sale)

    mock_update_products_discounted_prices_task.delay.assert_called_once_with(
        promotion.pk
    )


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_promotion_task"
)
def test_sale_channel_listing_add_update_remove_channels(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    sale_with_many_channels,
    permission_manage_discounts,
    channel_PLN,
    channel_USD,
    channel_JPY,
):
    # given
    sale = sale_with_many_channels
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    channel_jpy_id = graphene.Node.to_global_id("Channel", channel_JPY.id)
    discounted = 5

    channel_listing = SaleChannelListing.objects.filter(sale_id=sale.pk).order_by(
        "currency"
    )
    assert len(channel_listing) == 2
    assert channel_listing[0].channel_id == channel_PLN.id
    assert channel_listing[1].channel_id == channel_USD.id
    convert_sales_to_promotions()

    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [
                {"channelId": channel_usd_id, "discountValue": discounted},
                {"channelId": channel_jpy_id, "discountValue": discounted},
            ],
            "removeChannels": [channel_pln_id],
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
    assert not content["data"]["saleChannelListingUpdate"]["errors"]
    data = content["data"]["saleChannelListingUpdate"]["sale"]
    assert data["name"] == sale.name
    channel_listings = data["channelListings"]
    assert len(channel_listings) == 2
    assert all(
        [
            listing["channel"]["slug"] in [channel_USD.slug, channel_JPY.slug]
            for listing in channel_listings
        ]
    )
    assert all([listing["discountValue"] == discounted for listing in channel_listings])

    promotion = Promotion.objects.get(old_sale_id=sale.pk)
    rules = promotion.rules.all()
    assert len(rules) == 2
    for rule in rules:
        assert len(rule.channels.all()) == 1


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
    convert_sales_to_promotions()

    channel_listing = SaleChannelListing.objects.get(
        sale_id=sale.pk, channel_id=channel_USD.id
    )
    assert channel_listing.discount_value == 5
    staff_api_client.user.user_permissions.add(permission_manage_discounts)

    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [
                {"channelId": channel_id, "discountValue": discounted_value}
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
    )

    # then
    assert_negative_positive_decimal_value(response)


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_promotion_task"
)
def test_sale_channel_listing_update_duplicated_ids_in_add_and_remove(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted = 10.11
    convert_sales_to_promotions()

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
    mock_update_products_discounted_prices_task.assert_not_called()


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_promotion_task"
)
def test_sale_channel_listing_update_duplicated_channel_in_add(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted = 10.11
    convert_sales_to_promotions()

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
    mock_update_products_discounted_prices_task.assert_not_called()


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_promotion_task"
)
def test_sale_channel_listing_update_duplicated_channel_in_remove(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    convert_sales_to_promotions()
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
    mock_update_products_discounted_prices_task.assert_not_called()


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_promotion_task"
)
def test_sale_channel_listing_update_with_invalid_decimal_places(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    discounted = 1.123
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    convert_sales_to_promotions()
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
    mock_update_products_discounted_prices_task.assert_not_called()


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_promotion_task"
)
def test_sale_channel_listing_update_with_invalid_percentage_value(
    mock_update_products_discounted_prices_task,
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
    convert_sales_to_promotions()
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
    mock_update_products_discounted_prices_task.assert_not_called()


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
    ".update_products_discounted_prices_of_promotion_task"
)
def test_invalidate_data_sale_channel_listings_update(
    mock_update_products_discounted_prices_task,
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
    convert_sales_to_promotions()
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
    promotion = Promotion.objects.get(old_sale_id=sale.id)
    rules = promotion.rules.all()
    assert len(rules) == 2
    old_rule = rules.get(old_channel_listing_id__isnull=True)
    new_rule = rules.get(old_channel_listing_id__isnull=False)
    assert old_rule.reward_value is None
    assert new_rule.reward_value == discount_value

    assert old_rule.channels.first() is None
    assert new_rule.channels.first().id == channel_USD.id
    assert len(new_rule.channels.all()) == 1

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
    mock_update_products_discounted_prices_task.delay.assert_called_once_with(
        promotion.pk,
    )


@patch(
    "saleor.graphql.discount.mutations.sale.sale_channel_listing_update"
    ".update_products_discounted_prices_of_promotion_task"
)
def test_sale_channel_listing_remove_all_channels_multiple_times(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_PLN,
    channel_USD,
):
    # Despite removing the promotion from all channels, we ensure at least one rule
    # is assigned to promotion in order to determine old sale's type and catalogue.
    # This test checks if only one rule remains when all channels are removed multiple
    # times.

    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    discounted = 2
    convert_sales_to_promotions()
    staff_api_client.user.user_permissions.add(permission_manage_discounts)
    query = SALE_CHANNEL_LISTING_UPDATE_MUTATION
    mock_update_products_discounted_prices_task.return_value = None

    variables_add = {
        "id": sale_id,
        "input": {
            "addChannels": [
                {"channelId": channel_usd_id, "discountValue": discounted},
                {"channelId": channel_pln_id, "discountValue": discounted},
            ]
        },
    }
    variables_remove = {
        "id": sale_id,
        "input": {"removeChannels": [channel_usd_id, channel_pln_id]},
    }

    # when
    staff_api_client.post_graphql(query, variables=variables_add)
    staff_api_client.post_graphql(query, variables=variables_remove)
    staff_api_client.post_graphql(query, variables=variables_add)
    staff_api_client.post_graphql(query, variables=variables_remove)

    # then
    promotion = Promotion.objects.get(old_sale_id=sale.pk)
    rules = promotion.rules.all()
    assert len(rules) == 1
    assert not rules[0].channels.first()
