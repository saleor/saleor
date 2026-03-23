from .....page.models import PageType
from ....tests.utils import assert_no_permission, get_graphql_content

RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION = """
    mutation returnReasonReferenceClear {
        returnReasonReferenceClear {
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


def test_return_reason_reference_type_clear_by_staff_success(
    staff_api_client, site_settings, permission_manage_settings, page_type
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    site_settings.return_reason_reference_type = page_type
    site_settings.save()
    assert site_settings.return_reason_reference_type == page_type

    # when
    response = staff_api_client.post_graphql(
        RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["returnReasonReferenceClear"]

    assert not data["errors"]
    assert data["returnSettings"]
    assert data["returnSettings"]["reasonReferenceType"] is None

    # Verify database update
    site_settings.refresh_from_db()
    assert site_settings.return_reason_reference_type is None


def test_return_reason_reference_type_clear_by_app_success(
    app_api_client, site_settings, permission_manage_settings, page_type
):
    # given
    app_api_client.app.permissions.add(permission_manage_settings)

    site_settings.return_reason_reference_type = page_type
    site_settings.save()
    assert site_settings.return_reason_reference_type == page_type

    # when
    response = app_api_client.post_graphql(
        RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["returnReasonReferenceClear"]

    assert not data["errors"]
    assert data["returnSettings"]
    assert data["returnSettings"]["reasonReferenceType"] is None

    # Verify database update
    site_settings.refresh_from_db()
    assert site_settings.return_reason_reference_type is None


def test_return_reason_reference_type_clear_when_already_none(
    staff_api_client, site_settings, permission_manage_settings
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    site_settings.return_reason_reference_type = None
    site_settings.save()
    assert site_settings.return_reason_reference_type is None

    # when
    response = staff_api_client.post_graphql(
        RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["returnReasonReferenceClear"]

    assert not data["errors"]
    assert data["returnSettings"]
    assert data["returnSettings"]["reasonReferenceType"] is None

    # Verify database state remains unchanged
    site_settings.refresh_from_db()
    assert site_settings.return_reason_reference_type is None


def test_return_reason_reference_type_clear_multiple_page_types(
    staff_api_client, site_settings, permission_manage_settings
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    page_type1 = PageType.objects.create(name="Type 1", slug="type-1")
    page_type2 = PageType.objects.create(name="Type 2", slug="type-2")

    site_settings.return_reason_reference_type = page_type1
    site_settings.save()
    assert site_settings.return_reason_reference_type == page_type1

    # when
    response = staff_api_client.post_graphql(
        RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["returnReasonReferenceClear"]

    assert not data["errors"]
    assert data["returnSettings"]
    assert data["returnSettings"]["reasonReferenceType"] is None

    # Verify database update
    site_settings.refresh_from_db()
    assert site_settings.return_reason_reference_type is None

    # Verify other page types still exist
    assert PageType.objects.filter(id=page_type1.id).exists()
    assert PageType.objects.filter(id=page_type2.id).exists()


def test_return_reason_reference_type_clear_no_permission_staff(
    staff_api_client,
):
    # when
    response = staff_api_client.post_graphql(
        RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION
    )

    # then
    assert_no_permission(response)


def test_return_reason_reference_type_clear_no_permission_customer(
    user_api_client,
):
    # when
    response = user_api_client.post_graphql(RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION)

    # then
    assert_no_permission(response)


def test_return_reason_reference_type_clear_no_permission_anonymous(
    api_client,
):
    # when
    response = api_client.post_graphql(RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION)

    # then
    assert_no_permission(response)


def test_return_reason_reference_type_clear_app_no_permission(
    app_api_client,
):
    # when
    response = app_api_client.post_graphql(RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION)

    # then
    assert_no_permission(response)
