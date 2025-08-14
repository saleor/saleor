import graphene

from .....page.models import PageType
from ....tests.utils import assert_no_permission, get_graphql_content

REFUND_SETTINGS_UPDATE_MUTATION = """
    mutation refundSettingsUpdate($input: RefundSettingsUpdateInput!) {
        refundSettingsUpdate(input: $input) {
            refundSettings {
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


def test_refund_settings_update_by_staff_success(
    staff_api_client, site_settings, permission_manage_settings, page_type
):
    """Test successful refund settings update by staff user."""
    # given
    assert site_settings.refund_reason_reference_type is None
    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"refundReasonReferenceType": page_type_id}}

    # when
    response = staff_api_client.post_graphql(
        REFUND_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_settings,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["refundSettingsUpdate"]

    assert not data["errors"]
    assert data["refundSettings"]
    assert data["refundSettings"]["reasonReferenceType"]["id"] == page_type_id
    assert data["refundSettings"]["reasonReferenceType"]["name"] == page_type.name
    assert data["refundSettings"]["reasonReferenceType"]["slug"] == page_type.slug

    # Verify database update
    site_settings.refresh_from_db()
    assert site_settings.refund_reason_reference_type == page_type


def test_refund_settings_update_by_app_success(
    app_api_client, site_settings, permission_manage_settings, page_type
):
    """Test successful refund settings update by app."""
    # given
    assert site_settings.refund_reason_reference_type is None
    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"refundReasonReferenceType": page_type_id}}

    # when
    response = app_api_client.post_graphql(
        REFUND_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_settings,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["refundSettingsUpdate"]

    assert not data["errors"]
    assert data["refundSettings"]
    assert data["refundSettings"]["reasonReferenceType"]["id"] == page_type_id

    # Verify database update
    site_settings.refresh_from_db()
    assert site_settings.refund_reason_reference_type == page_type


def test_refund_settings_update_change_page_type(
    staff_api_client, site_settings, permission_manage_settings, page_type
):
    """Test updating refund settings to a different page type."""
    # given - set initial page type
    initial_page_type = PageType.objects.create(name="Initial Type", slug="initial-type")
    site_settings.refund_reason_reference_type = initial_page_type
    site_settings.save()

    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"refundReasonReferenceType": page_type_id}}

    # when
    response = staff_api_client.post_graphql(
        REFUND_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_settings,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["refundSettingsUpdate"]

    assert not data["errors"]
    assert data["refundSettings"]["reasonReferenceType"]["id"] == page_type_id

    # Verify database update
    site_settings.refresh_from_db()
    assert site_settings.refund_reason_reference_type == page_type


def test_refund_settings_update_empty_id_success(
    staff_api_client, permission_manage_settings, site_settings
):
    """Test successful update when providing empty ID (clears the setting)."""
    # given
    variables = {"input": {"refundReasonReferenceType": ""}}

    # when
    response = staff_api_client.post_graphql(
        REFUND_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_settings,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["refundSettingsUpdate"]

    assert not data["errors"]
    assert data["refundSettings"]
    assert data["refundSettings"]["reasonReferenceType"] is None


def test_refund_settings_update_invalid_id_format(
    staff_api_client, permission_manage_settings
):
    """Test validation error when providing invalid ID format."""
    # given
    variables = {"input": {"refundReasonReferenceType": "invalid-id-format"}}

    # when
    response = staff_api_client.post_graphql(
        REFUND_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_settings,),
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content


def test_refund_settings_update_nonexistent_page_type(
    staff_api_client, permission_manage_settings
):
    """Test validation error when PageType doesn't exist."""
    # given
    nonexistent_id = graphene.Node.to_global_id("PageType", 99999)
    variables = {"input": {"refundReasonReferenceType": nonexistent_id}}

    # when
    response = staff_api_client.post_graphql(
        REFUND_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_settings,),
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content


def test_refund_settings_update_wrong_model_type(
    staff_api_client, permission_manage_settings, product
):
    """Test validation error when providing ID of wrong model type."""
    # given
    product_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"input": {"refundReasonReferenceType": product_id}}

    # when
    response = staff_api_client.post_graphql(
        REFUND_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_settings,),
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content


def test_refund_settings_update_no_permission_staff(
    staff_api_client, page_type
):
    """Test permission denied for staff without proper permissions."""
    # given
    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"refundReasonReferenceType": page_type_id}}

    # when
    response = staff_api_client.post_graphql(
        REFUND_SETTINGS_UPDATE_MUTATION, variables
    )

    # then
    assert_no_permission(response)


def test_refund_settings_update_no_permission_customer(
    user_api_client, page_type
):
    """Test permission denied for customer users."""
    # given
    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"refundReasonReferenceType": page_type_id}}

    # when
    response = user_api_client.post_graphql(
        REFUND_SETTINGS_UPDATE_MUTATION, variables
    )

    # then
    assert_no_permission(response)


def test_refund_settings_update_no_permission_anonymous(
    api_client, page_type
):
    """Test permission denied for anonymous users."""
    # given
    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"refundReasonReferenceType": page_type_id}}

    # when
    response = api_client.post_graphql(
        REFUND_SETTINGS_UPDATE_MUTATION, variables
    )

    # then
    assert_no_permission(response)


def test_refund_settings_update_app_no_permission(
    app_api_client, page_type
):
    """Test permission denied for app without proper permissions."""
    # given
    page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    variables = {"input": {"refundReasonReferenceType": page_type_id}}

    # when
    response = app_api_client.post_graphql(
        REFUND_SETTINGS_UPDATE_MUTATION, variables
    )

    # then
    assert_no_permission(response)
