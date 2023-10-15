import graphene

from .....app.models import App
from .....core.jwt import create_access_token_for_app
from ....tests.fixtures import ApiClient
from ....tests.utils import assert_no_permission
from . import PUBLIC_KEY, PUBLIC_VALUE
from .test_delete_metadata import (
    execute_clear_public_metadata_for_item,
    item_without_public_metadata,
)
from .test_delete_private_metadata import (
    execute_clear_private_metadata_for_item,
    item_without_private_metadata,
)
from .test_update_metadata import (
    UPDATE_PUBLIC_METADATA_MUTATION,
    execute_update_public_metadata_for_item,
    item_contains_proper_public_metadata,
)
from .test_update_private_metadata import (
    UPDATE_PRIVATE_METADATA_MUTATION,
    execute_update_private_metadata_for_item,
    item_contains_proper_private_metadata,
)


def test_delete_private_metadata_for_app(staff_api_client, permission_manage_apps, app):
    # given
    app.store_value_in_private_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    app.save(update_fields=["private_metadata"])
    app_id = graphene.Node.to_global_id("App", app.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_apps,
        app_id,
        "App",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        app,
        app_id,
    )


def test_delete_public_metadata_for_app(staff_api_client, permission_manage_apps, app):
    # given
    app.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    app.save(update_fields=["metadata"])
    app_id = graphene.Node.to_global_id("App", app.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_apps,
        app_id,
        "App",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], app, app_id
    )


def test_add_public_metadata_for_sale(
    staff_api_client, permission_manage_discounts, promotion_converted_from_sale
):
    # given
    promotion = promotion_converted_from_sale
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_discounts, sale_id, "Sale"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        promotion_converted_from_sale,
        sale_id,
    )


def test_add_public_metadata_for_app(staff_api_client, permission_manage_apps, app):
    # given
    app_id = graphene.Node.to_global_id("App", app.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_apps,
        app_id,
        "App",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], app, app_id
    )


def test_add_public_metadata_for_app_by_different_app(
    app_api_client, permission_manage_apps, app, payment_app
):
    # given
    app_id = graphene.Node.to_global_id("App", payment_app.pk)
    app_api_client.app = app

    # when
    response = execute_update_public_metadata_for_item(
        app_api_client,
        permission_manage_apps,
        app_id,
        "App",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], payment_app, app_id
    )


def test_add_public_metadata_for_app_that_is_owner(
    app_api_client, permission_manage_apps, app
):
    # given
    app_id = graphene.Node.to_global_id("App", app.pk)
    app_api_client.app = app

    # when
    response = execute_update_public_metadata_for_item(
        app_api_client,
        None,
        app_id,
        "App",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], app, app_id
    )


def test_add_public_metadata_for_app_by_staff_without_permissions(
    staff_api_client, app
):
    # given
    app_id = graphene.Node.to_global_id("App", app.pk)
    variables = {
        "id": app_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "App", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_add_public_metadata_for_app_with_app_user_token(app, staff_user):
    # given
    token = create_access_token_for_app(app, staff_user)
    api_client = ApiClient(user=staff_user)
    api_client.token = token
    app_id = graphene.Node.to_global_id("App", app.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client,
        None,
        app_id,
        "App",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], app, app_id
    )


def test_add_public_metadata_for_unrelated_app_by_app_user_token(staff_user, app):
    # given
    token = create_access_token_for_app(app, staff_user)
    api_client = ApiClient(user=staff_user)
    api_client.token = token
    second_app = App.objects.create(name="Sample app", is_active=True)
    app_id = graphene.Node.to_global_id("App", second_app.pk)

    variables = {
        "id": app_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "App", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_add_private_metadata_for_app_by_different_app(
    app_api_client, permission_manage_apps, app, payment_app
):
    # given
    app_id = graphene.Node.to_global_id("App", payment_app.pk)
    app_api_client.app = app

    # when
    response = execute_update_private_metadata_for_item(
        app_api_client,
        permission_manage_apps,
        app_id,
        "App",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        payment_app,
        app_id,
    )


def test_add_private_metadata_for_app_with_app_user_token(
    staff_user, permission_manage_apps, app, payment_app
):
    # given
    token = create_access_token_for_app(app, staff_user)
    api_client = ApiClient(user=staff_user)
    api_client.token = token
    app_id = graphene.Node.to_global_id("App", app.pk)

    variables = {
        "id": app_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "App", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_add_private_metadata_by_app_that_is_owner(
    app_api_client, permission_manage_apps, app
):
    # given
    app_id = graphene.Node.to_global_id("App", app.pk)
    app_api_client.app = app

    # when
    response = execute_update_private_metadata_for_item(
        app_api_client,
        None,
        app_id,
        "App",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        app,
        app_id,
    )


def test_add_private_metadata_for_app(staff_api_client, permission_manage_apps, app):
    # given
    app_id = graphene.Node.to_global_id("App", app.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_apps,
        app_id,
        "App",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        app,
        app_id,
    )
