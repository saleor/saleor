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


def test_by_staff_success(
    staff_api_client, site_settings, permission_manage_settings, page_type
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    site_settings.return_reason_reference_type = page_type
    site_settings.save()

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

    site_settings.refresh_from_db()
    assert site_settings.return_reason_reference_type is None


def test_by_app_success(
    app_api_client, site_settings, permission_manage_settings, page_type
):
    # given
    app_api_client.app.permissions.add(permission_manage_settings)

    site_settings.return_reason_reference_type = page_type
    site_settings.save()

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

    site_settings.refresh_from_db()
    assert site_settings.return_reason_reference_type is None


def test_when_already_none(staff_api_client, site_settings, permission_manage_settings):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_settings)

    site_settings.return_reason_reference_type = None
    site_settings.save()

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

    site_settings.refresh_from_db()
    assert site_settings.return_reason_reference_type is None


def test_no_permission_staff(
    staff_api_client,
):
    # when
    response = staff_api_client.post_graphql(
        RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION
    )

    # then
    assert_no_permission(response)


def test_no_permission_customer(
    user_api_client,
):
    # when
    response = user_api_client.post_graphql(RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION)

    # then
    assert_no_permission(response)


def test_no_permission_anonymous(
    api_client,
):
    # when
    response = api_client.post_graphql(RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION)

    # then
    assert_no_permission(response)


def test_app_no_permission(
    app_api_client,
):
    # when
    response = app_api_client.post_graphql(RETURN_REASON_REFERENCE_TYPE_CLEAR_MUTATION)

    # then
    assert_no_permission(response)
