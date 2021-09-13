import graphene

from ..jwt import create_access_token_for_app_extension, jwt_decode


def test_create_access_token_for_app_extension_staff_user_with_more_permissions(
    app_with_extensions,
    staff_user,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_channels,
):
    # given
    staff_user.user_permissions.set(
        [permission_manage_channels, permission_manage_apps, permission_manage_products]
    )
    app, extensions = app_with_extensions
    extension = extensions[0]
    extension.permissions.set([permission_manage_products])

    # when
    access_token = create_access_token_for_app_extension(
        app_extension=extension,
        permissions=extension.permissions.all(),
        user=staff_user,
    )

    # then
    decoded_token = jwt_decode(access_token, verify_expiration=False)
    assert decoded_token["permissions"] == ["MANAGE_PRODUCTS"]
    _, decode_extension_id = graphene.Node.from_global_id(
        decoded_token["app_extension"]
    )
    assert int(decode_extension_id) == extension.id


def test_create_access_token_for_app_extension_with_more_permissions(
    app_with_extensions,
    staff_user,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_channels,
):
    # given
    staff_user.user_permissions.set([permission_manage_products])
    app, extensions = app_with_extensions
    extension = extensions[0]
    extension.permissions.set(
        [permission_manage_channels, permission_manage_apps, permission_manage_products]
    )

    # when
    access_token = create_access_token_for_app_extension(
        app_extension=extension,
        permissions=extension.permissions.all(),
        user=staff_user,
    )

    # then
    decoded_token = jwt_decode(access_token, verify_expiration=False)
    assert decoded_token["permissions"] == ["MANAGE_PRODUCTS"]
    _, decode_extension_id = graphene.Node.from_global_id(
        decoded_token["app_extension"]
    )
    assert int(decode_extension_id) == extension.id
