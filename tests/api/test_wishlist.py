import graphene
import pytest

from saleor.wishlist.models import Wishlist

from .utils import assert_no_permission, get_graphql_content


@pytest.mark.skip(reason="Wishlist temporary removed from api")
def test_wishlist_add_variant_to_anonymous_user(api_client, variant):
    query = """
    mutation WishlistAddVariant($variant_id: ID!) {
        wishlistAddVariant(variantId: $variant_id) {
            errors{
                field
                message
            }
            wishlist {
                id
            }
        }
    }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"variant_id": variant_id}
    response = api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


@pytest.mark.skip(reason="Wishlist temporary removed from api")
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
            wishlist {
                id
            }
        }
    }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"variant_id": variant_id}
    response = user_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    items = content["data"]["wishlistAddVariant"]["wishlist"]
    assert len(items) == 1
    _, item_id = graphene.Node.from_global_id(items[0]["id"])
    # Assert that user has a single wishlist item
    user.refresh_from_db()
    wishlist = user.wishlist
    assert wishlist.items.count() == 1
    item = wishlist.items.first()
    assert item_id == str(item.pk)


@pytest.mark.skip(reason="Wishlist temporary removed from api")
def test_wishlist_remove_variant_from_anonymous_user(
    api_client, customer_wishlist_item
):
    assert customer_wishlist_item.variants.count() == 1
    query = """
    mutation WishlistRemoveVariant($variant_id: ID!) {
        wishlistRemoveVariant(variantId: $variant_id) {
            errors{
                field
                message
            }
            wishlist {
                id
            }
        }
    }
    """
    variant = customer_wishlist_item.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"variant_id": variant_id}
    response = api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


@pytest.mark.skip(reason="Wishlist temporary removed from api")
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
            wishlist {
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
    items = content["data"]["wishlistRemoveVariant"]["wishlist"]
    assert len(items) == 0
    # Check that the wishlist_item was removed together with the only variant
    assert wishlist.items.count() == 0


@pytest.mark.skip(reason="Wishlist temporary removed from api")
def test_wishlist_add_product_to_logged_user(user_api_client, product):
    user = user_api_client.user
    # Assert that user doesn't have a wishlist
    with pytest.raises(Wishlist.DoesNotExist):
        user.wishlist
    query = """
    mutation WishlistAddProduct($product_id: ID!) {
        wishlistAddProduct(productId: $product_id) {
            errors{
                field
                message
            }
            wishlist {
                id
            }
        }
    }
    """
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {"product_id": product_id}
    response = user_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    items = content["data"]["wishlistAddProduct"]["wishlist"]
    assert len(items) == 1
    _, item_id = graphene.Node.from_global_id(items[0]["id"])
    # Assert that user has a single wishlist item
    user.refresh_from_db()
    wishlist = user.wishlist
    assert wishlist.items.count() == 1
    item = wishlist.items.first()
    assert item_id == str(item.pk)


@pytest.mark.skip(reason="Wishlist temporary removed from api")
def test_wishlist_remove_product_from_logged_user(
    user_api_client, customer_wishlist_item
):
    user = user_api_client.user
    wishlist = customer_wishlist_item.wishlist
    # Assert initial conditions are correct
    assert user.wishlist == wishlist
    assert wishlist.items.count() == 1
    query = """
    mutation WishlistRemoveProduct($product_id: ID!) {
        wishlistRemoveProduct(productId: $product_id) {
            errors{
                field
                message
            }
            wishlist {
                id
            }
        }
    }
    """
    product = customer_wishlist_item.product
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {"product_id": product_id}
    response = user_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    items = content["data"]["wishlistRemoveProduct"]["wishlist"]
    assert len(items) == 0
    # Check that the wishlist_item was removed
    assert wishlist.items.count() == 0


@pytest.mark.skip(reason="Wishlist temporary removed from api")
def test_wishlist_get_items_from_anonymous_user(api_client):
    query = """
    query WishlistItems {
        me {
            wishlist(first: 10) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    }
    """
    response = api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content["data"]["me"] is None


@pytest.mark.skip(reason="Wishlist temporary removed from api")
def test_wishlist_get_items_from_logged_user(user_api_client, customer_wishlist_item):
    user = user_api_client.user
    wishlist = customer_wishlist_item.wishlist
    # Assert initial conditions are correct
    assert user.wishlist == wishlist
    assert wishlist.items.count() == 1
    query = """
    query WishlistItems {
        me {
            wishlist(first: 10) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["me"]["wishlist"]
    assert len(data["edges"]) == 1
    wishlist_item_id = graphene.Node.to_global_id(
        "WishlistItem", customer_wishlist_item.pk
    )
    assert data["edges"][0]["node"]["id"] == wishlist_item_id
