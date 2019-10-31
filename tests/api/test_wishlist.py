import graphene
import pytest

from saleor.wishlist.models import Wishlist
from saleor.wishlist.session_helpers import WishlistSessionHelper

from .utils import get_graphql_content


def test_wishlist_add_variant_to_anonymous_user(api_client, variant):
    # Assert that there is no wishlist in the session
    assert WishlistSessionHelper(api_client.session).get_wishlist() is None
    query = """
    mutation WishlistAddVariant($variant_id: ID!) {
        wishlistAddVariant(variantId: $variant_id) {
            errors{
                field
                message
            }
            wishlistItems {
                id
            }
        }
    }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"variant_id": variant_id}
    response = api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    items = content["data"]["wishlistAddVariant"]["wishlistItems"]
    assert len(items) == 1
    _, item_id = graphene.Node.from_global_id(items[0]["id"])
    # Assert that there is a single wishlist item in the session
    wishlist = WishlistSessionHelper(api_client.session).get_wishlist()
    assert wishlist.items.count() == 1
    item = wishlist.items.first()
    assert item_id == str(item.pk)


def test_wishlist_add_variant_to_logged_user(user_api_client, variant):
    user = user_api_client.user
    # Assert that user doesn't have a wishlist
    with pytest.raises(Wishlist.DoesNotExist):
        user.wishlist
    query = """
    mutation WishlistAddVariant($variant_id: ID!) {
        wishlistAddVariant(variantId: $variant_id) {
            errors{
                field
                message
            }
            wishlistItems {
                id
            }
        }
    }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"variant_id": variant_id}
    response = user_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    items = content["data"]["wishlistAddVariant"]["wishlistItems"]
    assert len(items) == 1
    _, item_id = graphene.Node.from_global_id(items[0]["id"])
    # Assert that user has a single wishlist item
    user.refresh_from_db()
    wishlist = user.wishlist
    assert wishlist.items.count() == 1
    item = wishlist.items.first()
    assert item_id == str(item.pk)


def test_wishlist_remove_variant_from_anonymous_user(api_client, variant):
    # Add Wishlist items to the session
    wishlist = WishlistSessionHelper(api_client.session).get_or_create_wishlist()
    wishlist.add_variant(variant)
    assert wishlist.items.count() == 1
    query = """
    mutation WishlistRemoveVariant($variant_id: ID!) {
        wishlistRemoveVariant(variantId: $variant_id) {
            errors{
                field
                message
            }
            wishlistItems {
                id
            }
        }
    }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"variant_id": variant_id}
    response = api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    items = content["data"]["wishlistRemoveVariant"]["wishlistItems"]
    assert len(items) == 0
    # Assert that the wishlist item was removed
    wishlist = WishlistSessionHelper(api_client.session).get_wishlist()
    assert wishlist.items.count() == 0


def test_wishlist_remove_variant_from_logged_user(
    user_api_client, customer_wishlist_item
):
    user = user_api_client.user
    wishlist = customer_wishlist_item.wishlist
    # Assert initial conditions are correct
    assert user.wishlist == wishlist
    assert wishlist.items.count() == 1
    query = """
    mutation WishlistRemoveVariant($variant_id: ID!) {
        wishlistRemoveVariant(variantId: $variant_id) {
            errors{
                field
                message
            }
            wishlistItems {
                id
            }
        }
    }
    """
    variant = customer_wishlist_item.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"variant_id": variant_id}
    response = user_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    items = content["data"]["wishlistRemoveVariant"]["wishlistItems"]
    assert len(items) == 0
    # Check that the wishlist_item was removed together with the only variant
    assert wishlist.items.count() == 0


def test_wishlist_get_items_from_anonymous_user(api_client, variant):
    # Add variant to the wishlist from the session
    wishlist = WishlistSessionHelper(api_client.session).get_or_create_wishlist()
    wishlist.add_variant(variant)
    assert wishlist.items.count() == 1
    wishlist_item = wishlist.items.first()
    query = """
    query WishlistItems {
        wishlistItems(first: 10) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    response = api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["wishlistItems"]
    assert len(data["edges"]) == 1
    wishlist_item_id = graphene.Node.to_global_id("WishlistItem", wishlist_item.pk)
    assert data["edges"][0]["node"]["id"] == wishlist_item_id


def test_wishlist_get_items_from_logged_user(user_api_client, customer_wishlist_item):
    user = user_api_client.user
    wishlist = customer_wishlist_item.wishlist
    # Assert initial conditions are correct
    assert user.wishlist == wishlist
    assert wishlist.items.count() == 1
    query = """
    query WishlistItems {
        wishlistItems(first: 10) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["wishlistItems"]
    assert len(data["edges"]) == 1
    wishlist_item_id = graphene.Node.to_global_id(
        "WishlistItem", customer_wishlist_item.pk
    )
    assert data["edges"][0]["node"]["id"] == wishlist_item_id
