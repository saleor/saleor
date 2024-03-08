import graphene

from .....discount import RewardValueType
from .....discount.error_codes import DiscountErrorCode
from .....product.models import ProductChannelListing
from ....tests.utils import assert_negative_positive_decimal_value, get_graphql_content
from ...utils import get_products_for_rule

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


def test_sale_channel_listing_add_channels(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_PLN,
):
    # given
    promotion = promotion_converted_from_sale
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
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
    assert not content["data"]["saleChannelListingUpdate"]["errors"]
    data = content["data"]["saleChannelListingUpdate"]["sale"]
    assert data["name"] == promotion.name

    channel_listing = data["channelListings"]
    discounts = [item["discountValue"] for item in channel_listing]
    slugs = [item["channel"]["slug"] for item in channel_listing]
    assert discounted in discounts
    assert channel_PLN.slug in slugs

    promotion.refresh_from_db()
    rules = promotion.rules.all()
    assert len(rules) == 2
    assert (
        len({(rule.reward_value_type, str(rule.catalogue_predicate)) for rule in rules})
        == 1
    )
    assert all([rule.old_channel_listing_id for rule in rules])

    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


def test_sale_channel_listing_add_multiple_channels(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_PLN,
    channel_JPY,
):
    # given
    promotion = promotion_converted_from_sale
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    channel_jpy_id = graphene.Node.to_global_id("Channel", channel_JPY.id)
    discounted = 5

    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [
                {"channelId": channel_pln_id, "discountValue": discounted},
                {"channelId": channel_jpy_id, "discountValue": discounted},
            ]
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
    assert data["name"] == promotion.name

    channel_listing = data["channelListings"]
    discounts = [item["discountValue"] for item in channel_listing]
    slugs = [item["channel"]["slug"] for item in channel_listing]
    assert discounted in discounts
    assert channel_PLN.slug in slugs
    assert channel_JPY.slug in slugs

    promotion.refresh_from_db()
    rules = promotion.rules.all()
    assert len(rules) == 3
    old_channel_listing_ids = [rule.old_channel_listing_id for rule in rules]
    assert all(old_channel_listing_ids)
    assert len(set(old_channel_listing_ids)) == 3

    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


def test_sale_channel_listing_update_channels(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    promotion = promotion_converted_from_sale
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted = 10.11

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

    channel_listing = data["channelListings"]

    assert len(channel_listing) == 1
    assert channel_listing[0]["discountValue"] == discounted
    assert channel_listing[0]["channel"]["slug"] == channel_USD.slug

    promotion.refresh_from_db()
    rules = promotion.rules.all()
    assert len(rules) == 1

    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


def test_sale_channel_listing_remove_channels(
    staff_api_client,
    promotion_converted_from_sale_with_many_channels,
    permission_manage_discounts,
    channel_USD,
    channel_PLN,
):
    # given
    promotion = promotion_converted_from_sale_with_many_channels
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    rule = promotion.rules.filter(channels=channel_PLN).get()
    product_ids = list(get_products_for_rule(rule).values_list("id", flat=True))
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
    assert data["name"] == promotion.name

    channel_listing = data["channelListings"]
    assert len(channel_listing) == 1
    assert channel_listing[0]["channel"]["slug"] == channel_PLN.slug

    promotion.refresh_from_db()
    rules = promotion.rules.all()
    assert len(rules) == 1
    assert not ProductChannelListing.objects.filter(
        product_id__in=product_ids,
        channel_id=channel_USD.id,
        discounted_price_dirty=False,
    )


def test_sale_channel_listing_remove_all_channels(
    staff_api_client,
    promotion_converted_from_sale_with_many_channels,
    permission_manage_discounts,
    channel_USD,
    channel_PLN,
):
    # given
    promotion = promotion_converted_from_sale_with_many_channels
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.id)
        for channel in [channel_USD, channel_PLN]
    ]

    rule = promotion.rules.first()
    reward_value_type = rule.reward_value_type
    predicate = rule.catalogue_predicate

    rule = promotion.rules.filter(channels=channel_PLN).get()
    product_ids = list(get_products_for_rule(rule).values_list("id", flat=True))

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
    assert data["name"] == promotion.name
    assert not data["channelListings"]

    promotion.refresh_from_db()
    # Despite removing the promotion from all channels, we ensure at least one rule
    # is assigned to promotion in order to determine old sale's type and catalogue
    rules = promotion.rules.all()
    assert len(rules) == 1
    assert rules[0].reward_value_type == reward_value_type
    assert rules[0].catalogue_predicate == predicate

    assert not ProductChannelListing.objects.filter(
        product_id__in=product_ids,
        channel_id=channel_USD.id,
        discounted_price_dirty=False,
    )


def test_sale_channel_listing_add_update_remove_channels(
    staff_api_client,
    promotion_converted_from_sale_with_many_channels,
    permission_manage_discounts,
    channel_PLN,
    channel_USD,
    channel_JPY,
):
    # given
    promotion = promotion_converted_from_sale_with_many_channels
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    channel_jpy_id = graphene.Node.to_global_id("Channel", channel_JPY.id)
    discounted = 5

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
    assert data["name"] == promotion.name
    channel_listings = data["channelListings"]
    assert len(channel_listings) == 2
    assert all(
        [
            listing["channel"]["slug"] in [channel_USD.slug, channel_JPY.slug]
            for listing in channel_listings
        ]
    )
    assert all([listing["discountValue"] == discounted for listing in channel_listings])

    promotion.refresh_from_db()
    rules = promotion.rules.all()
    assert len(rules) == 2
    for rule in rules:
        assert len(rule.channels.all()) == 1

    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


def test_sale_channel_listing_update_with_negative_discounted_value(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    promotion = promotion_converted_from_sale
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted_value = -10
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


def test_sale_channel_listing_update_duplicated_ids_in_add_and_remove(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    promotion = promotion_converted_from_sale
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
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

    for rule in promotion.rules.all():
        assert rule.variants_dirty is False


def test_sale_channel_listing_update_duplicated_channel_in_add(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    promotion = promotion_converted_from_sale
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
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
    for rule in promotion.rules.all():
        assert rule.variants_dirty is False


def test_sale_channel_listing_update_duplicated_channel_in_remove(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    promotion = promotion_converted_from_sale
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
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
    for rule in promotion.rules.all():
        assert rule.variants_dirty is False


def test_sale_channel_listing_update_with_invalid_decimal_places(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    promotion = promotion_converted_from_sale
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
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
    for rule in promotion.rules.all():
        assert rule.variants_dirty is False


def test_sale_channel_listing_update_with_invalid_percentage_value(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    promotion = promotion_converted_from_sale
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
    rule = promotion.rules.first()
    rule.reward_value_type = RewardValueType.PERCENTAGE
    rule.save(update_fields=["reward_value_type"])
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
    for rule in promotion.rules.all():
        assert rule.variants_dirty is False


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


def test_invalidate_data_sale_channel_listings_update(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    discount_value = 10
    promotion = promotion_converted_from_sale
    rule = promotion.rules.first()
    rule_name = rule.name
    rule.channels.remove(channel_USD)

    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
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
    promotion.refresh_from_db()
    rules = promotion.rules.all()
    assert len(rules) == 2
    old_rule = rules.get(name=rule_name)
    new_rule = rules.get(name__isnull=True)

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
    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


def test_sale_channel_listing_remove_all_channels_multiple_times(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_PLN,
    channel_USD,
):
    # Despite removing the promotion from all channels, we ensure at least one rule
    # is assigned to promotion in order to determine old sale's type and catalogue.
    # This test checks if only one rule remains when all channels are removed multiple
    # times.

    # given
    promotion = promotion_converted_from_sale
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    discounted = 2
    staff_api_client.user.user_permissions.add(permission_manage_discounts)
    query = SALE_CHANNEL_LISTING_UPDATE_MUTATION

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
    promotion.refresh_from_db()
    rules = promotion.rules.all()
    assert len(rules) == 1
    assert not rules[0].channels.first()

    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


def test_sale_channel_listing_update_not_found_error(
    staff_api_client,
    permission_manage_discounts,
):
    # given
    query = SALE_CHANNEL_LISTING_UPDATE_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Sale", "0"),
        "input": {"removeChannels": []},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleChannelListingUpdate"]["sale"]
    errors = content["data"]["saleChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == DiscountErrorCode.NOT_FOUND.name
