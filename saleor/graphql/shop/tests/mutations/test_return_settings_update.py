import graphene

from .....page.models import PageType
from ....tests.utils import assert_no_permission, get_graphql_content

RETURN_SETTINGS_UPDATE_MUTATION = """
    mutation returnSettingsUpdate($input: ReturnSettingsUpdateInput!) {
        returnSettingsUpdate(input: $input) {
            returnSettings {
                reasonReferenceType {
                    id
                    name
                    slug
                }
            }
            errors {
                code
                field
                message
            }
        }
    }
"""


def test_return_settings_update_by_staff_success(
    staff_api_client, site_settings, permission_manage_settings, page_type
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    assert site_settings.return_reason_reference_type is None
    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"returnReasonReferenceType": page_type_id}}

    # when
    response = staff_api_client.post_graphql(
        RETURN_SETTINGS_UPDATE_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["returnSettingsUpdate"]

    assert not data["errors"]
    assert data["returnSettings"]
    assert data["returnSettings"]["reasonReferenceType"]["id"] == page_type_id
    assert data["returnSettings"]["reasonReferenceType"]["name"] == page_type.name
    assert data["returnSettings"]["reasonReferenceType"]["slug"] == page_type.slug

    # Verify database update
    site_settings.refresh_from_db()
    assert site_settings.return_reason_reference_type == page_type


def test_return_settings_update_by_app_success(
    app_api_client, site_settings, permission_manage_settings, page_type
):
    # given
    app_api_client.app.permissions.add(permission_manage_settings)

    assert site_settings.return_reason_reference_type is None
    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"returnReasonReferenceType": page_type_id}}

    # when
    response = app_api_client.post_graphql(
        RETURN_SETTINGS_UPDATE_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["returnSettingsUpdate"]

    assert not data["errors"]
    assert data["returnSettings"]
    assert data["returnSettings"]["reasonReferenceType"]["id"] == page_type_id

    # Verify database update
    site_settings.refresh_from_db()
    assert site_settings.return_reason_reference_type == page_type


def test_return_settings_update_change_page_type(
    staff_api_client, site_settings, permission_manage_settings, page_type
):
    # given - set initial page type
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    initial_page_type = PageType.objects.create(
        name="Initial Type", slug="initial-type"
    )
    site_settings.return_reason_reference_type = initial_page_type
    site_settings.save()

    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"returnReasonReferenceType": page_type_id}}

    # when
    response = staff_api_client.post_graphql(
        RETURN_SETTINGS_UPDATE_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["returnSettingsUpdate"]

    assert not data["errors"]
    assert data["returnSettings"]["reasonReferenceType"]["id"] == page_type_id

    # Verify database update
    site_settings.refresh_from_db()
    assert site_settings.return_reason_reference_type == page_type


def test_return_settings_update_empty_id_success(
    staff_api_client, permission_manage_settings, site_settings
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    variables = {"input": {"returnReasonReferenceType": ""}}

    # when
    response = staff_api_client.post_graphql(
        RETURN_SETTINGS_UPDATE_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["returnSettingsUpdate"]

    assert not data["errors"]
    assert data["returnSettings"]
    assert data["returnSettings"]["reasonReferenceType"] is None


def test_return_settings_update_invalid_id_format(
    staff_api_client, permission_manage_settings
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    variables = {"input": {"returnReasonReferenceType": "invalid-id-format"}}

    # when
    response = staff_api_client.post_graphql(
        RETURN_SETTINGS_UPDATE_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content


def test_return_settings_update_nonexistent_page_type(
    staff_api_client, permission_manage_settings
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    nonexistent_id = graphene.Node.to_global_id("PageType", 99999)
    variables = {"input": {"returnReasonReferenceType": nonexistent_id}}

    # when
    response = staff_api_client.post_graphql(
        RETURN_SETTINGS_UPDATE_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content


def test_return_settings_update_wrong_page_type(
    staff_api_client, permission_manage_settings, product
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    product_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"input": {"returnReasonReferenceType": product_id}}

    # when
    response = staff_api_client.post_graphql(
        RETURN_SETTINGS_UPDATE_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content


def test_return_settings_update_no_permission_staff(staff_api_client, page_type):
    # given
    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"returnReasonReferenceType": page_type_id}}

    # when
    response = staff_api_client.post_graphql(RETURN_SETTINGS_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_return_settings_update_no_permission_customer(user_api_client, page_type):
    # given
    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"returnReasonReferenceType": page_type_id}}

    # when
    response = user_api_client.post_graphql(RETURN_SETTINGS_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_return_settings_update_no_permission_anonymous(api_client, page_type):
    # given
    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"returnReasonReferenceType": page_type_id}}

    # when
    response = api_client.post_graphql(RETURN_SETTINGS_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_return_settings_update_app_no_permission(app_api_client, page_type):
    # given
    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"returnReasonReferenceType": page_type_id}}

    # when
    response = app_api_client.post_graphql(RETURN_SETTINGS_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)
