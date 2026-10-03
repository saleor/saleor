"""READ_TRANSLATIONS permission model (translations domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ_TRANSLATIONS sees the same reads as MANAGE_TRANSLATIONS
  B. No write leak - READ_TRANSLATIONS is rejected by MANAGE_TRANSLATIONS mutations
  C. Regression    - MANAGE_TRANSLATIONS behavior unchanged; no-perms still denied
  G. Grant-scope   - MANAGE_TRANSLATIONS covers granting its READ_TRANSLATIONS twin

The `translations` / `translation` queries are gated through
`PermissionsField(permissions=[MANAGE_TRANSLATIONS])` (auto-widened at
`core/fields.py`). These tests lock the parity in.
"""

import graphene

from ....permission.enums import SitePermissions
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

TRANSLATIONS_QUERY = """
    query {
        translations(kind: PRODUCT, first: 10) {
            edges {
                node {
                    __typename
                    ... on ProductTranslatableContent { productId }
                }
            }
        }
    }
"""

PRODUCT_TRANSLATE_MUTATION = """
    mutation ($id: ID!, $input: TranslationInput!, $lang: LanguageCodeEnum!) {
        productTranslate(id: $id, input: $input, languageCode: $lang) {
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
# A. Parity - READ_TRANSLATIONS sees the same reads as MANAGE_TRANSLATIONS
# --------------------------------------------------------------------------- #


def test_read_translations_lists_translations(
    staff_api_client, product, permission_read_translations
):
    # given a translatable product and a staff user holding only READ_TRANSLATIONS
    staff_api_client.user.user_permissions.add(permission_read_translations)

    # when listing translatable items
    response = staff_api_client.post_graphql(TRANSLATIONS_QUERY)

    # then the product's translatable content is returned (parity with MANAGE)
    content = get_graphql_content(response)
    edges = content["data"]["translations"]["edges"]
    product_ids = {
        edge["node"]["productId"]
        for edge in edges
        if edge["node"]["__typename"] == "ProductTranslatableContent"
    }
    assert product_ids == {graphene.Node.to_global_id("Product", product.pk)}


# --------------------------------------------------------------------------- #
# B. No write leak - READ_TRANSLATIONS is rejected by MANAGE_TRANSLATIONS mutations
# --------------------------------------------------------------------------- #


def test_read_translations_cannot_translate_product(
    staff_api_client, product, permission_read_translations
):
    # given a staff user holding only READ_TRANSLATIONS
    from ....product.models import ProductTranslation

    staff_api_client.user.user_permissions.add(permission_read_translations)
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "input": {"name": "Nazwa"},
        "lang": "PL",
    }

    # when attempting a MANAGE_TRANSLATIONS mutation
    response = staff_api_client.post_graphql(PRODUCT_TRANSLATE_MUTATION, variables)

    # then it is denied and no translation is created
    assert_no_permission(response)
    assert not ProductTranslation.objects.filter(
        product=product, language_code="pl"
    ).exists()


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_TRANSLATIONS unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_translations_still_lists_translations(
    staff_api_client, product, permission_manage_translations
):
    # given a translatable product and a staff user holding MANAGE_TRANSLATIONS (baseline)
    staff_api_client.user.user_permissions.add(permission_manage_translations)

    # when listing translatable items
    response = staff_api_client.post_graphql(TRANSLATIONS_QUERY)

    # then the product's translatable content is returned (no regression)
    content = get_graphql_content(response)
    edges = content["data"]["translations"]["edges"]
    product_ids = {
        edge["node"]["productId"]
        for edge in edges
        if edge["node"]["__typename"] == "ProductTranslatableContent"
    }
    assert product_ids == {graphene.Node.to_global_id("Product", product.pk)}


def test_no_perms_staff_cannot_list_translations(staff_api_client, product):
    # given a staff user with no relevant permissions

    # when listing translatable items
    response = staff_api_client.post_graphql(TRANSLATIONS_QUERY)

    # then it is denied - adding the READ twin did not widen unprivileged access
    assert_no_permission(response)


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE_TRANSLATIONS covers granting its READ_TRANSLATIONS twin
# --------------------------------------------------------------------------- #


def test_app_create_read_translations_inferred_from_manage_translations(
    staff_api_client, permission_manage_apps, permission_manage_translations
):
    # given a staff user with MANAGE_APPS + MANAGE_TRANSLATIONS and NO READ_TRANSLATIONS
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_translations
    )
    variables = {
        "name": "read app",
        "permissions": [PermissionEnum.READ_TRANSLATIONS.name],
    }

    # when creating an app that should hold READ_TRANSLATIONS
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding read_translations - inferred from MANAGE
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_TRANSLATIONS.name}


def test_registry_maps_translations_twin():
    # given the registry entries
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then MANAGE_TRANSLATIONS maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[SitePermissions.MANAGE_TRANSLATIONS]
        == SitePermissions.READ_TRANSLATIONS
    )
