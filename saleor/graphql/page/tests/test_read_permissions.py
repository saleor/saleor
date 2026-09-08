"""READ_PAGES / READ_PAGE_TYPES_AND_ATTRIBUTES permission model (page domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ_X sees the same reads as MANAGE_X
  B. No write leak - READ_X is rejected by MANAGE_X mutations
  C. Regression    - MANAGE_X behavior unchanged; no-perms still denied
  E. Metadata      - READ_X unlocks private metadata reads (dynamic perm resolution)
  G. Grant-scope   - MANAGE_X covers granting its READ_X twin (appCreate scope check)

READ_PAGES parity is enforced through Page.visible_to_user (the "view unpublished
pages" row-filter). READ_PAGE_TYPES_AND_ATTRIBUTES parity is enforced through
Attribute.get_visible_to_user and the page-type attribute-field gates.
"""

import graphene

from ....permission.enums import PagePermissions
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

PAGE_QUERY = """
    query ($id: ID!) {
        page(id: $id) { id title }
    }
"""

PAGE_PRIVATE_META_QUERY = """
    query ($id: ID!) {
        page(id: $id) {
            id
            privateMetadata { key value }
        }
    }
"""

PAGE_UPDATE_MUTATION = """
    mutation ($id: ID!) {
        pageUpdate(id: $id, input: {title: "Changed"}) {
            page { id }
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

PAGE_TYPE_UPDATE_MUTATION = """
    mutation ($id: ID!) {
        pageTypeUpdate(id: $id, input: {name: "Changed"}) {
            pageType { id }
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


def test_read_pages_sees_unpublished_page(
    staff_api_client, page_list_unpublished, permission_read_pages
):
    # given a staff user holding only READ_PAGES
    unpublished_page = page_list_unpublished[0]
    staff_api_client.user.user_permissions.add(permission_read_pages)
    variables = {"id": graphene.Node.to_global_id("Page", unpublished_page.pk)}

    # when looking up an unpublished page by id
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)

    # then the unpublished page is returned (parity with MANAGE_PAGES)
    content = get_graphql_content(response)
    assert content["data"]["page"]["title"] == unpublished_page.title


def test_read_page_types_sees_non_storefront_attribute(
    staff_api_client, tag_page_attribute, permission_read_page_types_and_attributes
):
    # given a non-storefront page-type attribute and a READ_PAGE_TYPES-only staff user
    tag_page_attribute.visible_in_storefront = False
    tag_page_attribute.save(update_fields=["visible_in_storefront"])
    staff_api_client.user.user_permissions.add(
        permission_read_page_types_and_attributes
    )

    # when querying the attributes list
    response = staff_api_client.post_graphql(ATTRIBUTES_QUERY)

    # then the non-storefront attribute is visible (parity with MANAGE twin)
    content = get_graphql_content(response)
    slugs = {edge["node"]["slug"] for edge in content["data"]["attributes"]["edges"]}
    assert tag_page_attribute.slug in slugs


# --------------------------------------------------------------------------- #
# B. No write leak - READ_X is rejected by MANAGE_X mutations
# --------------------------------------------------------------------------- #


def test_read_pages_cannot_update_page(staff_api_client, page, permission_read_pages):
    # given a staff user holding only READ_PAGES
    staff_api_client.user.user_permissions.add(permission_read_pages)
    variables = {"id": graphene.Node.to_global_id("Page", page.pk)}

    # when attempting a MANAGE_PAGES mutation
    response = staff_api_client.post_graphql(PAGE_UPDATE_MUTATION, variables)

    # then it is denied and the record is unchanged
    assert_no_permission(response)
    page.refresh_from_db()
    assert page.title != "Changed"


def test_read_page_types_cannot_update_page_type(
    staff_api_client, page_type, permission_read_page_types_and_attributes
):
    # given a staff user holding only READ_PAGE_TYPES_AND_ATTRIBUTES
    staff_api_client.user.user_permissions.add(
        permission_read_page_types_and_attributes
    )
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when attempting a MANAGE twin mutation
    response = staff_api_client.post_graphql(PAGE_TYPE_UPDATE_MUTATION, variables)

    # then it is denied and the record is unchanged
    assert_no_permission(response)
    page_type.refresh_from_db()
    assert page_type.name != "Changed"


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_X unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_pages_still_sees_unpublished_page(
    staff_api_client, page_list_unpublished, permission_manage_pages
):
    # given a staff user holding MANAGE_PAGES (baseline)
    unpublished_page = page_list_unpublished[0]
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    variables = {"id": graphene.Node.to_global_id("Page", unpublished_page.pk)}

    # when looking up an unpublished page by id
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)

    # then the unpublished page is returned (no regression)
    content = get_graphql_content(response)
    assert content["data"]["page"]["title"] == unpublished_page.title


def test_no_perms_staff_cannot_see_unpublished_page(
    staff_api_client, page_list_unpublished
):
    # given a staff user with no relevant permissions
    unpublished_page = page_list_unpublished[0]
    variables = {"id": graphene.Node.to_global_id("Page", unpublished_page.pk)}

    # when looking up an unpublished page by id
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)

    # then it is invisible - adding READ twins did not widen unprivileged access
    content = get_graphql_content(response)
    assert content["data"]["page"] is None


# --------------------------------------------------------------------------- #
# E. Metadata - READ_X unlocks private metadata reads (dynamic perm resolution)
# --------------------------------------------------------------------------- #


def test_read_pages_reads_page_private_metadata(
    staff_api_client, page, permission_read_pages
):
    # given a page with private metadata and a READ_PAGES-only staff user
    page.store_value_in_private_metadata({"secret": "value"})
    page.save(update_fields=["private_metadata"])
    staff_api_client.user.user_permissions.add(permission_read_pages)
    variables = {"id": graphene.Node.to_global_id("Page", page.pk)}

    # when reading the page's private metadata
    response = staff_api_client.post_graphql(PAGE_PRIVATE_META_QUERY, variables)

    # then the private metadata is returned
    content = get_graphql_content(response)
    metadata = {
        item["key"]: item["value"]
        for item in content["data"]["page"]["privateMetadata"]
    }
    assert metadata["secret"] == "value"


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE_X covers granting its READ_X twin
# --------------------------------------------------------------------------- #


def test_app_create_read_pages_inferred_from_manage_pages(
    staff_api_client, permission_manage_apps, permission_manage_pages
):
    # given a staff user with MANAGE_APPS + MANAGE_PAGES and NO READ_PAGES
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_pages
    )
    variables = {
        "name": "read app",
        "permissions": [PermissionEnum.READ_PAGES.name],
    }

    # when creating an app that should hold READ_PAGES
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding read_pages - inferred from MANAGE_PAGES
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_PAGES.name}


def test_app_with_read_pages_can_read_unpublished_page(
    app_api_client, page_list_unpublished, permission_read_pages
):
    # given an app holding READ_PAGES
    unpublished_page = page_list_unpublished[0]
    app_api_client.app.permissions.add(permission_read_pages)
    variables = {"id": graphene.Node.to_global_id("Page", unpublished_page.pk)}

    # when looking up an unpublished page by id
    response = app_api_client.post_graphql(
        PAGE_QUERY, variables, check_no_permissions=False
    )

    # then the unpublished page is returned (apps are a primary target audience)
    content = get_graphql_content(response)
    assert content["data"]["page"]["title"] == unpublished_page.title


def test_registry_maps_page_twins():
    # given the registry entries
    from ....permission.enums import PageTypePermissions
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then each MANAGE maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[PagePermissions.MANAGE_PAGES]
        == PagePermissions.READ_PAGES
    )
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[
            PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES
        ]
        == PageTypePermissions.READ_PAGE_TYPES_AND_ATTRIBUTES
    )
