"""READ_CUSTOMER_TYPES_AND_ATTRIBUTES permission model (customer-type domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ twin sees the same reads as MANAGE twin
  B. No write leak - READ twin is rejected by MANAGE-only mutations
  C. Regression    - MANAGE twin behavior unchanged; no-perms hides storefront-hidden attrs
  G. Grant-scope   - MANAGE twin covers granting its READ twin (appCreate)

The read surface is `CustomerType.attributes`: its resolver gates storefront-hidden
attributes behind `one_of_permissions_or_auth_filter_required`, which does NOT
auto-expand, so the read gate is widened explicitly with `expand_read_permissions`.
These tests exercise that widened gate directly (hidden attribute visibility).
"""

import graphene

from ....permission.enums import CustomerTypePermissions
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

CUSTOMER_TYPE_ATTRIBUTES_QUERY = """
    query ($id: ID!) {
        customerType(id: $id) {
            attributes { slug }
        }
    }
"""

CUSTOMER_TYPE_CREATE_MUTATION = """
    mutation ($name: String!) {
        customerTypeCreate(input: {name: $name}) {
            customerType { id }
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

# customer_type_with_attributes bundles two storefront-visible attributes and one
# storefront-hidden attribute; only a permitted principal sees the hidden one.
VISIBLE_SLUGS = {"loyalty-level", "description"}
HIDDEN_SLUG = "internal-score"


# --------------------------------------------------------------------------- #
# A. Parity - READ twin sees the same reads as MANAGE twin (hidden attrs)
# --------------------------------------------------------------------------- #


def test_read_customer_types_reads_hidden_attributes(
    staff_api_client,
    customer_type_with_attributes,
    permission_read_customer_types_and_attributes,
):
    # given a customer type with a storefront-hidden attribute and a staff user
    # holding only the READ twin
    staff_api_client.user.user_permissions.add(
        permission_read_customer_types_and_attributes
    )
    variables = {
        "id": graphene.Node.to_global_id(
            "CustomerType", customer_type_with_attributes.pk
        )
    }

    # when reading the customer type attributes
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_ATTRIBUTES_QUERY, variables)

    # then the hidden attribute is included (parity with the MANAGE twin)
    content = get_graphql_content(response)
    slugs = {a["slug"] for a in content["data"]["customerType"]["attributes"]}
    assert slugs == VISIBLE_SLUGS | {HIDDEN_SLUG}


# --------------------------------------------------------------------------- #
# B. No write leak - READ twin is rejected by MANAGE-only mutations
# --------------------------------------------------------------------------- #


def test_read_customer_types_cannot_create_customer_type(
    staff_api_client, permission_read_customer_types_and_attributes
):
    # given a staff user holding only the READ twin
    from ....account.models import CustomerType

    staff_api_client.user.user_permissions.add(
        permission_read_customer_types_and_attributes
    )
    variables = {"name": "new type"}

    # when attempting a MANAGE-only mutation
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_CREATE_MUTATION, variables)

    # then it is denied and no customer type is created
    assert_no_permission(response)
    assert CustomerType.objects.filter(name="new type").exists() is False


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE twin unchanged; no-perms hides hidden attributes
# --------------------------------------------------------------------------- #


def test_manage_customer_types_still_reads_hidden_attributes(
    staff_api_client,
    customer_type_with_attributes,
    permission_manage_customer_types_and_attributes,
):
    # given a customer type and a staff user holding the MANAGE twin (baseline)
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {
        "id": graphene.Node.to_global_id(
            "CustomerType", customer_type_with_attributes.pk
        )
    }

    # when reading the customer type attributes
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_ATTRIBUTES_QUERY, variables)

    # then the hidden attribute is included (no regression)
    content = get_graphql_content(response)
    slugs = {a["slug"] for a in content["data"]["customerType"]["attributes"]}
    assert slugs == VISIBLE_SLUGS | {HIDDEN_SLUG}


def test_no_perms_staff_cannot_read_hidden_attributes(
    staff_api_client, customer_type_with_attributes
):
    # given a customer type and a staff user with no relevant permissions
    variables = {
        "id": graphene.Node.to_global_id(
            "CustomerType", customer_type_with_attributes.pk
        )
    }

    # when reading the customer type attributes
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_ATTRIBUTES_QUERY, variables)

    # then only storefront-visible attributes are returned - the READ twin did not
    # widen unprivileged access to the hidden attribute
    content = get_graphql_content(response)
    slugs = {a["slug"] for a in content["data"]["customerType"]["attributes"]}
    assert slugs == VISIBLE_SLUGS


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE twin covers granting its READ twin
# --------------------------------------------------------------------------- #


def test_app_create_read_twin_inferred_from_manage_twin(
    staff_api_client,
    permission_manage_apps,
    permission_manage_customer_types_and_attributes,
):
    # given a staff user with MANAGE_APPS + the MANAGE twin and NOT the READ twin
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_customer_types_and_attributes
    )
    variables = {
        "name": "read app",
        "permissions": [PermissionEnum.READ_CUSTOMER_TYPES_AND_ATTRIBUTES.name],
    }

    # when creating an app that should hold the READ twin
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding the READ twin - inferred from the MANAGE twin
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_CUSTOMER_TYPES_AND_ATTRIBUTES.name}


def test_registry_maps_customer_types_twin():
    # given the registry entries
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then the MANAGE twin maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[
            CustomerTypePermissions.MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES
        ]
        == CustomerTypePermissions.READ_CUSTOMER_TYPES_AND_ATTRIBUTES
    )
