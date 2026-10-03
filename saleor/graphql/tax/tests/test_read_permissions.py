"""READ_TAXES permission model (tax domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ_TAXES sees the same reads as MANAGE_TAXES
  B. No write leak - READ_TAXES is rejected by MANAGE_TAXES mutations
  C. Regression    - MANAGE_TAXES behavior unchanged; no-perms still denied
  E. Metadata      - READ_TAXES unlocks tax-class private metadata (dynamic perm resolution)
  G. Grant-scope   - MANAGE_TAXES covers granting its READ_TAXES twin (appCreate)

The tax queries themselves are gated only on authenticated staff/app, so the sole
MANAGE_TAXES read chokepoint is private metadata (resolved through the
`expand_read_permissions` meta map). These tests lock that parity in.
"""

import graphene

from ....permission.enums import CheckoutPermissions
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

TAX_CLASS_PRIVATE_META_QUERY = """
    query ($id: ID!) {
        taxClass(id: $id) {
            id
            privateMetadata { key value }
        }
    }
"""

TAX_CLASS_DELETE_MUTATION = """
    mutation ($id: ID!) {
        taxClassDelete(id: $id) {
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
# A/E. Parity - READ_TAXES reads tax-class private metadata
# --------------------------------------------------------------------------- #


def test_read_taxes_reads_tax_class_private_metadata(
    staff_api_client, default_tax_class, permission_read_taxes
):
    # given a tax class with private metadata and a READ_TAXES-only staff user
    tax_class = default_tax_class
    tax_class.store_value_in_private_metadata({"secret": "value"})
    tax_class.save(update_fields=["private_metadata"])
    staff_api_client.user.user_permissions.add(permission_read_taxes)
    variables = {"id": graphene.Node.to_global_id("TaxClass", tax_class.pk)}

    # when reading the tax class's private metadata
    response = staff_api_client.post_graphql(TAX_CLASS_PRIVATE_META_QUERY, variables)

    # then the private metadata is returned (parity with MANAGE_TAXES)
    content = get_graphql_content(response)
    metadata = {
        item["key"]: item["value"]
        for item in content["data"]["taxClass"]["privateMetadata"]
    }
    assert metadata["secret"] == "value"


# --------------------------------------------------------------------------- #
# B. No write leak - READ_TAXES is rejected by MANAGE_TAXES mutations
# --------------------------------------------------------------------------- #


def test_read_taxes_cannot_delete_tax_class(
    staff_api_client, default_tax_class, permission_read_taxes
):
    # given a staff user holding only READ_TAXES
    from ....tax.models import TaxClass

    tax_class = default_tax_class
    staff_api_client.user.user_permissions.add(permission_read_taxes)
    variables = {"id": graphene.Node.to_global_id("TaxClass", tax_class.pk)}

    # when attempting a MANAGE_TAXES mutation
    response = staff_api_client.post_graphql(TAX_CLASS_DELETE_MUTATION, variables)

    # then it is denied and the tax class is unchanged
    assert_no_permission(response)
    assert TaxClass.objects.filter(pk=tax_class.pk).exists()


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_TAXES unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_taxes_still_reads_tax_class_private_metadata(
    staff_api_client, default_tax_class, permission_manage_taxes
):
    # given a tax class with private metadata and a MANAGE_TAXES staff user (baseline)
    tax_class = default_tax_class
    tax_class.store_value_in_private_metadata({"secret": "value"})
    tax_class.save(update_fields=["private_metadata"])
    staff_api_client.user.user_permissions.add(permission_manage_taxes)
    variables = {"id": graphene.Node.to_global_id("TaxClass", tax_class.pk)}

    # when reading the tax class's private metadata
    response = staff_api_client.post_graphql(TAX_CLASS_PRIVATE_META_QUERY, variables)

    # then the private metadata is returned (no regression)
    content = get_graphql_content(response)
    metadata = {
        item["key"]: item["value"]
        for item in content["data"]["taxClass"]["privateMetadata"]
    }
    assert metadata["secret"] == "value"


def test_no_perms_staff_cannot_read_tax_class_private_metadata(
    staff_api_client, default_tax_class
):
    # given a tax class with private metadata and a staff user with no relevant perms
    tax_class = default_tax_class
    tax_class.store_value_in_private_metadata({"secret": "value"})
    tax_class.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("TaxClass", tax_class.pk)}

    # when reading the tax class's private metadata
    response = staff_api_client.post_graphql(TAX_CLASS_PRIVATE_META_QUERY, variables)

    # then it is denied - adding the READ twin did not widen unprivileged access
    assert_no_permission(response)


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE_TAXES covers granting its READ_TAXES twin
# --------------------------------------------------------------------------- #


def test_app_create_read_taxes_inferred_from_manage_taxes(
    staff_api_client, permission_manage_apps, permission_manage_taxes
):
    # given a staff user with MANAGE_APPS + MANAGE_TAXES and NO READ_TAXES
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_taxes
    )
    variables = {"name": "read app", "permissions": [PermissionEnum.READ_TAXES.name]}

    # when creating an app that should hold READ_TAXES
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding read_taxes - inferred from MANAGE_TAXES
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_TAXES.name}


def test_registry_maps_taxes_twin():
    # given the registry entries
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then MANAGE_TAXES maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[CheckoutPermissions.MANAGE_TAXES]
        == CheckoutPermissions.READ_TAXES
    )
