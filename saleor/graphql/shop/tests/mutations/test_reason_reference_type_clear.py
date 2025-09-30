from .....page.models import PageType
from ....tests.utils import assert_no_permission, get_graphql_content

REFUND_REASON_REFERENCE_TYPE_CLEAR_MUTATION = """
    mutation refundReasonReferenceClear {
        refundReasonReferenceClear {
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


def test_refund_reason_reference_type_clear_by_staff_success(
    staff_api_client, site_settings, permission_manage_settings, page_type
):
    """Test successful clearing of refund reason reference type by staff user."""
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    # Set initial page type
    site_settings.refund_reason_reference_type = page_type
    site_settings.save()
    assert site_settings.refund_reason_reference_type == page_type

    # when
    response = staff_api_client.post_graphql(
        REFUND_REASON_REFERENCE_TYPE_CLEAR_MUTATION,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["refundReasonReferenceClear"]

    assert not data["errors"]
    assert data["refundSettings"]
    assert data["refundSettings"]["reasonReferenceType"] is None

    # Verify database update
    site_settings.refresh_from_db()
    assert site_settings.refund_reason_reference_type is None


def test_refund_reason_reference_type_clear_by_app_success(
    app_api_client, site_settings, permission_manage_settings, page_type
):
    """Test successful clearing of refund reason reference type by app."""
    # given
    app_api_client.app.permissions.add(permission_manage_settings)

    # Set initial page type
    site_settings.refund_reason_reference_type = page_type
    site_settings.save()
    assert site_settings.refund_reason_reference_type == page_type

    # when
    response = app_api_client.post_graphql(
        REFUND_REASON_REFERENCE_TYPE_CLEAR_MUTATION,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["refundReasonReferenceClear"]

    assert not data["errors"]
    assert data["refundSettings"]
    assert data["refundSettings"]["reasonReferenceType"] is None

    # Verify database update
    site_settings.refresh_from_db()
    assert site_settings.refund_reason_reference_type is None


def test_refund_reason_reference_type_clear_when_already_none(
    staff_api_client, site_settings, permission_manage_settings
):
    """Test clearing when refund reason reference type is already None."""
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    # Ensure it's already None
    site_settings.refund_reason_reference_type = None
    site_settings.save()
    assert site_settings.refund_reason_reference_type is None

    # when
    response = staff_api_client.post_graphql(
        REFUND_REASON_REFERENCE_TYPE_CLEAR_MUTATION,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["refundReasonReferenceClear"]

    assert not data["errors"]
    assert data["refundSettings"]
    assert data["refundSettings"]["reasonReferenceType"] is None

    # Verify database state remains unchanged
    site_settings.refresh_from_db()
    assert site_settings.refund_reason_reference_type is None


def test_refund_reason_reference_type_clear_multiple_page_types(
    staff_api_client, site_settings, permission_manage_settings
):
    """Test clearing when multiple page types exist."""
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    # Create multiple page types
    page_type1 = PageType.objects.create(name="Type 1", slug="type-1")
    page_type2 = PageType.objects.create(name="Type 2", slug="type-2")

    # Set one as the reference type
    site_settings.refund_reason_reference_type = page_type1
    site_settings.save()
    assert site_settings.refund_reason_reference_type == page_type1

    # when
    response = staff_api_client.post_graphql(
        REFUND_REASON_REFERENCE_TYPE_CLEAR_MUTATION,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["refundReasonReferenceClear"]

    assert not data["errors"]
    assert data["refundSettings"]
    assert data["refundSettings"]["reasonReferenceType"] is None

    # Verify database update
    site_settings.refresh_from_db()
    assert site_settings.refund_reason_reference_type is None

    # Verify other page types still exist
    assert PageType.objects.filter(id=page_type1.id).exists()
    assert PageType.objects.filter(id=page_type2.id).exists()


def test_refund_reason_reference_type_clear_no_permission_staff(
    staff_api_client,
):
    """Test permission denied for staff without proper permissions."""
    # when
    response = staff_api_client.post_graphql(
        REFUND_REASON_REFERENCE_TYPE_CLEAR_MUTATION
    )

    # then
    assert_no_permission(response)


def test_refund_reason_reference_type_clear_no_permission_customer(
    user_api_client,
):
    """Test permission denied for customer users."""
    # when
    response = user_api_client.post_graphql(REFUND_REASON_REFERENCE_TYPE_CLEAR_MUTATION)

    # then
    assert_no_permission(response)


def test_refund_reason_reference_type_clear_no_permission_anonymous(
    api_client,
):
    """Test permission denied for anonymous users."""
    # when
    response = api_client.post_graphql(REFUND_REASON_REFERENCE_TYPE_CLEAR_MUTATION)

    # then
    assert_no_permission(response)


def test_refund_reason_reference_type_clear_app_no_permission(
    app_api_client,
):
    """Test permission denied for app without proper permissions."""
    # when
    response = app_api_client.post_graphql(REFUND_REASON_REFERENCE_TYPE_CLEAR_MUTATION)

    # then
    assert_no_permission(response)
