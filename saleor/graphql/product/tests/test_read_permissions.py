"""READ_PRODUCTS / READ_PRODUCT_TYPES_AND_ATTRIBUTES permission model (product domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ_X sees the same reads as MANAGE_X
  B. No write leak - READ_X is rejected by MANAGE_X mutations
  C. Regression    - MANAGE_X behavior unchanged; no-perms still denied
  E. Metadata      - READ_X unlocks private metadata reads (dynamic perm resolution)
  G. Grant-scope   - MANAGE_X covers granting its READ_X twin (appCreate scope check)

READ_PRODUCTS parity is enforced through ALL_PRODUCTS_PERMISSIONS (the "view all
products including unpublished" bundle) which is registry-widened, plus the
attribute-visibility gates. READ_PRODUCT_TYPES_AND_ATTRIBUTES parity is enforced
through Attribute.get_visible_to_user and the attribute-field permission decorator.
"""

import graphene

from ....permission.enums import ProductPermissions
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

PRODUCT_QUERY = """
    query ($id: ID!, $channel: String) {
        product(id: $id, channel: $channel) { id name }
    }
"""

PRODUCT_PRIVATE_META_QUERY = """
    query ($id: ID!, $channel: String) {
        product(id: $id, channel: $channel) {
            id
            privateMetadata { key value }
        }
    }
"""

PRODUCT_UPDATE_MUTATION = """
    mutation ($id: ID!) {
        productUpdate(id: $id, input: {name: "Changed"}) {
            product { id }
            errors { field code }
        }
    }
"""

ATTRIBUTES_QUERY = """
    query {
        attributes(first: 50) {
            edges { node { id slug visibleInStorefront } }
        }
    }
"""

ATTRIBUTE_UPDATE_MUTATION = """
    mutation ($id: ID!) {
        attributeUpdate(id: $id, input: {name: "Changed"}) {
            attribute { id }
            errors { field code }
        }
    }
"""

APP_CREATE_MUTATION = """
    mutation AppCreate($name: String, $permissions: [PermissionEnum!]) {
        appCreate(input: {name: $name, permissions: $permissions}) {
            app { permissions { code } }
            errors { field code permissions }
        }
    }
"""


# --------------------------------------------------------------------------- #
# A. Parity - READ_X sees the same reads as MANAGE_X
# --------------------------------------------------------------------------- #


def test_read_products_sees_unpublished_product(
    staff_api_client, unavailable_product, permission_read_products, channel_USD
):
    # given a staff user holding only READ_PRODUCTS
    staff_api_client.user.user_permissions.add(permission_read_products)
    variables = {
        "id": graphene.Node.to_global_id("Product", unavailable_product.pk),
        "channel": channel_USD.slug,
    }

    # when looking up an unpublished product by id
    response = staff_api_client.post_graphql(PRODUCT_QUERY, variables)

    # then the unpublished product is returned (parity with MANAGE_PRODUCTS)
    content = get_graphql_content(response)
    assert content["data"]["product"]["name"] == unavailable_product.name


def test_read_product_types_sees_non_storefront_attribute(
    staff_api_client, color_attribute, permission_read_product_types_and_attributes
):
    # given a non-storefront attribute and a READ_PRODUCT_TYPES-only staff user
    color_attribute.visible_in_storefront = False
    color_attribute.save(update_fields=["visible_in_storefront"])
    staff_api_client.user.user_permissions.add(
        permission_read_product_types_and_attributes
    )

    # when querying the attributes list
    response = staff_api_client.post_graphql(ATTRIBUTES_QUERY)

    # then the non-storefront attribute is visible (parity with MANAGE twin)
    content = get_graphql_content(response)
    slugs = {edge["node"]["slug"] for edge in content["data"]["attributes"]["edges"]}
    assert color_attribute.slug in slugs


# --------------------------------------------------------------------------- #
# B. No write leak - READ_X is rejected by MANAGE_X mutations
# --------------------------------------------------------------------------- #


def test_read_products_cannot_update_product(
    staff_api_client, product, permission_read_products
):
    # given a staff user holding only READ_PRODUCTS
    staff_api_client.user.user_permissions.add(permission_read_products)
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when attempting a MANAGE_PRODUCTS mutation
    response = staff_api_client.post_graphql(PRODUCT_UPDATE_MUTATION, variables)

    # then it is denied and the record is unchanged
    assert_no_permission(response)
    product.refresh_from_db()
    assert product.name != "Changed"


def test_read_product_types_cannot_update_attribute(
    staff_api_client, color_attribute, permission_read_product_types_and_attributes
):
    # given a staff user holding only READ_PRODUCT_TYPES_AND_ATTRIBUTES
    staff_api_client.user.user_permissions.add(
        permission_read_product_types_and_attributes
    )
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when attempting a MANAGE twin mutation
    response = staff_api_client.post_graphql(ATTRIBUTE_UPDATE_MUTATION, variables)

    # then it is denied and the record is unchanged
    assert_no_permission(response)
    color_attribute.refresh_from_db()
    assert color_attribute.name != "Changed"


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_X unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_products_still_sees_unpublished_product(
    staff_api_client, unavailable_product, permission_manage_products, channel_USD
):
    # given a staff user holding MANAGE_PRODUCTS (baseline)
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("Product", unavailable_product.pk),
        "channel": channel_USD.slug,
    }

    # when looking up an unpublished product by id
    response = staff_api_client.post_graphql(PRODUCT_QUERY, variables)

    # then the unpublished product is returned (no regression)
    content = get_graphql_content(response)
    assert content["data"]["product"]["name"] == unavailable_product.name


def test_no_perms_staff_cannot_see_unpublished_product(
    staff_api_client, unavailable_product, channel_USD
):
    # given a staff user with no relevant permissions
    variables = {
        "id": graphene.Node.to_global_id("Product", unavailable_product.pk),
        "channel": channel_USD.slug,
    }

    # when looking up an unpublished product by id
    response = staff_api_client.post_graphql(PRODUCT_QUERY, variables)

    # then it is invisible - adding READ twins did not widen unprivileged access
    content = get_graphql_content(response)
    assert content["data"]["product"] is None


# --------------------------------------------------------------------------- #
# E. Metadata - READ_X unlocks private metadata reads (dynamic perm resolution)
# --------------------------------------------------------------------------- #


def test_read_products_reads_product_private_metadata(
    staff_api_client, product, permission_read_products, channel_USD
):
    # given a product with private metadata and a READ_PRODUCTS-only staff user
    product.store_value_in_private_metadata({"secret": "value"})
    product.save(update_fields=["private_metadata"])
    staff_api_client.user.user_permissions.add(permission_read_products)
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when reading the product's private metadata
    response = staff_api_client.post_graphql(PRODUCT_PRIVATE_META_QUERY, variables)

    # then the private metadata is returned
    content = get_graphql_content(response)
    metadata = {
        item["key"]: item["value"]
        for item in content["data"]["product"]["privateMetadata"]
    }
    assert metadata["secret"] == "value"


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE_X covers granting its READ_X twin
# --------------------------------------------------------------------------- #


def test_app_create_read_products_inferred_from_manage_products(
    staff_api_client, permission_manage_apps, permission_manage_products
):
    # given a staff user with MANAGE_APPS + MANAGE_PRODUCTS and NO READ_PRODUCTS
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_products
    )
    variables = {
        "name": "read app",
        "permissions": [PermissionEnum.READ_PRODUCTS.name],
    }

    # when creating an app that should hold READ_PRODUCTS
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding read_products - inferred from MANAGE_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_PRODUCTS.name}


def test_app_with_read_products_can_read_unpublished_product(
    app_api_client, unavailable_product, permission_read_products, channel_USD
):
    # given an app holding READ_PRODUCTS
    app_api_client.app.permissions.add(permission_read_products)
    variables = {
        "id": graphene.Node.to_global_id("Product", unavailable_product.pk),
        "channel": channel_USD.slug,
    }

    # when looking up an unpublished product by id
    response = app_api_client.post_graphql(
        PRODUCT_QUERY, variables, check_no_permissions=False
    )

    # then the unpublished product is returned (apps are a primary target audience)
    content = get_graphql_content(response)
    assert content["data"]["product"]["name"] == unavailable_product.name


def test_registry_maps_product_twins():
    # given the registry entries
    from ....permission.enums import ProductTypePermissions
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then each MANAGE maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[ProductPermissions.MANAGE_PRODUCTS]
        == ProductPermissions.READ_PRODUCTS
    )
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[
            ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES
        ]
        == ProductTypePermissions.READ_PRODUCT_TYPES_AND_ATTRIBUTES
    )
