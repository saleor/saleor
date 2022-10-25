import graphene
import jwt
from cryptography.hazmat.primitives import serialization
from django.urls import reverse

from ..jwt import create_access_token_for_app_extension, jwt_decode, jwt_encode
from ..utils import build_absolute_uri


def test_create_access_token_for_app_extension_staff_user_with_more_permissions(
    app_with_extensions,
    staff_user,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_channels,
    site_settings,
):
    # given
    staff_user.user_permissions.set(
        [permission_manage_channels, permission_manage_apps, permission_manage_products]
    )
    audience = f"https://{site_settings.site.domain}.com/app-123"
    app, extensions = app_with_extensions
    app.audience = audience
    app.save()

    extension = extensions[0]
    extension.permissions.set([permission_manage_products])

    # when
    access_token = create_access_token_for_app_extension(
        app_extension=extension,
        permissions=extension.permissions.all(),
        user=staff_user,
        app=app,
    )

    # then
    decoded_token = jwt_decode(access_token, verify_expiration=False, verify_aud=False)
    assert decoded_token["permissions"] == ["MANAGE_PRODUCTS"]
    _, decode_extension_id = graphene.Node.from_global_id(
        decoded_token["app_extension"]
    )
    assert set(decoded_token["user_permissions"]) == set(
        ["MANAGE_CHANNELS", "MANAGE_APPS", "MANAGE_PRODUCTS"]
    )
    assert int(decode_extension_id) == extension.id
    assert decoded_token["aud"] == audience
    assert decoded_token["iss"] == build_absolute_uri(reverse("api"))


def test_create_access_token_for_app_extension_with_more_permissions(
    app_with_extensions,
    staff_user,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_channels,
    site_settings,
):
    # given
    staff_user.user_permissions.set([permission_manage_products])

    audience = f"https://{site_settings.site.domain}.com/app-123"
    app, extensions = app_with_extensions
    app.audience = audience
    app.save()

    extension = extensions[0]
    extension.permissions.set(
        [permission_manage_channels, permission_manage_apps, permission_manage_products]
    )

    # when
    access_token = create_access_token_for_app_extension(
        app_extension=extension,
        permissions=extension.permissions.all(),
        user=staff_user,
        app=app,
    )

    # then
    decoded_token = jwt_decode(access_token, verify_expiration=False)
    assert decoded_token["permissions"] == ["MANAGE_PRODUCTS"]
    _, decode_extension_id = graphene.Node.from_global_id(
        decoded_token["app_extension"]
    )
    assert decoded_token["user_permissions"] == ["MANAGE_PRODUCTS"]
    assert int(decode_extension_id) == extension.id
    assert decoded_token["aud"] == audience


def test_jwt_decode_accepts_token_signed_with_hs256(settings):
    # given
    payload = {"1": "A", "2": "B"}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    # when
    decoded_token = jwt_decode(token)

    # then
    assert payload == decoded_token


def test_jwt_decode_accepts_token_signed_with_rs256(settings):
    # given
    private_key = serialization.load_pem_private_key(
        settings.RSA_PRIVATE_KEY.encode("utf-8"), password=settings.RSA_PRIVATE_PASSWORD
    )
    payload = {"1": "A", "2": "B"}
    token = jwt.encode(payload, private_key, algorithm="RS256")

    # when
    decoded_token = jwt_decode(token)

    # then
    assert payload == decoded_token


def test_jwt_decode_accepts_app_token_rs256_with_audience(settings):
    # given
    private_key = serialization.load_pem_private_key(
        settings.RSA_PRIVATE_KEY.encode("utf-8"), password=settings.RSA_PRIVATE_PASSWORD
    )
    payload = {"1": "A", "2": "B", "aud": "tmp"}
    token = jwt.encode(payload, private_key, algorithm="RS256")

    # when & then
    # expected to not raise an exception
    jwt_decode(token)


def test_jwt_decode_accepts_app_token_hs256_with_audience(settings):
    # given
    payload = {"1": "A", "2": "B", "aud": "tmp"}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    # when & then
    # expected to not raise an exception
    jwt_decode(token)


def test_jwt_encode_creates_token_signed_with_rs256(settings):
    # given
    payload = {"1": "A", "2": "B"}

    # when
    token = jwt_encode(payload)

    # then
    headers = jwt.get_unverified_header(token)
    assert headers.get("alg") == "RS256"
