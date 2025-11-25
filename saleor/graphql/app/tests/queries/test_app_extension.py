import graphene
import pytest

from .....app.models import App, AppExtension
from .....app.types import AppExtensionMount, AppExtensionTarget, AppType
from .....core.jwt import jwt_decode
from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_APP_EXTENSION = """
query ($id: ID!){
    appExtension(id: $id){
        label
        url
        mount
        target
        mountName
        targetName
        id
        accessToken
        permissions{
            code
        }
        settings
        options {
          ... on AppExtensionOptionsWidget{
            widgetTarget {
              method
            }
          }
          ...on AppExtensionOptionsNewTab {
            newTabTarget{
              method
            }
          }

        }
    }
}
"""


def test_app_extension_staff_user(app, staff_api_client, permission_manage_products):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
        http_target_method="POST",
        target=AppExtensionTarget.WIDGET,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]
    assert app_extension.label == extension_data["label"]
    assert app_extension.url == extension_data["url"]
    assert app_extension.mount == extension_data["mount"].lower()
    assert app_extension.target == extension_data["target"].lower()

    assert app_extension.permissions.count() == 1
    assert len(extension_data["permissions"]) == 1
    permission_code = extension_data["permissions"][0]["code"].lower()
    assert app_extension.permissions.first().codename == permission_code

    assert extension_data["options"]["widgetTarget"]["method"] == "POST"

    assert extension_data["settings"] is not None
    assert extension_data["settings"]["widgetTarget"]["method"] == "POST"

    assert extension_data["mountName"] == "PRODUCT_OVERVIEW_MORE_ACTIONS"
    assert extension_data["targetName"] == "WIDGET"


def test_app_extension_by_app(app, app_api_client, permission_manage_products):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]
    assert app_extension.label == extension_data["label"]
    assert app_extension.url == extension_data["url"]
    assert app_extension.mount == extension_data["mount"].lower()
    assert app_extension.target == extension_data["target"].lower()

    assert app_extension.permissions.count() == 1
    assert len(extension_data["permissions"]) == 1
    permission_code = extension_data["permissions"][0]["code"].lower()
    assert app_extension.permissions.first().codename == permission_code

    assert extension_data["settings"] == {}

    assert extension_data["mountName"] == "PRODUCT_OVERVIEW_MORE_ACTIONS"
    assert extension_data["targetName"] == "POPUP"


def test_app_extensions_app_removed_app(
    staff_api_client, removed_app, permission_manage_products
):
    # given
    app_extension = AppExtension.objects.create(
        app=removed_app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]
    assert extension_data is None


def test_app_extension_normal_user(app, user_api_client, permission_manage_products):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = user_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
    )

    # then
    assert_no_permission(response)


def test_app_extension_staff_user_without_all_permissions(
    app, staff_api_client, permission_manage_products, permission_manage_orders
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
        permissions=[permission_manage_orders],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]
    assert extension_data["accessToken"] is None


def test_app_extension_staff_user_fetching_access_token(
    app,
    staff_api_client,
    permission_manage_orders,
    permission_manage_products,
    permission_manage_apps,
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products, permission_manage_orders)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
        permissions=[
            permission_manage_orders,
            permission_manage_products,
            permission_manage_apps,
        ],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]

    assert extension_data["accessToken"]
    decoded_token = jwt_decode(extension_data["accessToken"])
    assert set(decoded_token["permissions"]) == {"MANAGE_PRODUCTS", "MANAGE_ORDERS"}


def test_app_extension_access_token_with_audience(
    app,
    staff_api_client,
    permission_manage_orders,
    permission_manage_products,
    permission_manage_apps,
    site_settings,
):
    # given
    app.audience = f"https://{site_settings.site.domain}.com/app-123"
    app.save()
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products, permission_manage_orders)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
        permissions=[
            permission_manage_orders,
            permission_manage_products,
            permission_manage_apps,
        ],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]

    assert extension_data["accessToken"]
    decoded_token = jwt_decode(extension_data["accessToken"])
    assert decoded_token["aud"] == app.audience


def test_app_extension_staff_user_partial_permission(
    app,
    staff_api_client,
    permission_manage_orders,
    permission_manage_products,
    permission_manage_apps,
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products, permission_manage_orders)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
        permissions=[permission_manage_orders, permission_manage_apps],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]

    assert extension_data["accessToken"] is None


QUERY_APP_EXTENSION_WITH_APP = """
query ($id: ID!){
    appExtension(id: $id){
        label
        url
        mount
        target
        id
        permissions{
            code
        }
        app{
            id
        }
    }
}
"""


def test_app_extension_with_app_query_by_staff_without_permissions(
    app, staff_api_client, permission_manage_products
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION_WITH_APP,
        variables,
    )

    # then
    response = get_graphql_content(response)

    assert response["data"]["appExtension"]["id"] == id


def test_app_extension_with_app_query_by_app_without_permissions(
    app, app_api_client, permission_manage_products
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_EXTENSION_WITH_APP,
        variables,
    )

    # then
    response = get_graphql_content(response)

    # Can access OWN extension
    assert response["data"]["appExtension"]["id"] == id


def test_app_extension_with_app_query_by_app_without_permissions_other_app(
    app_api_client, permission_manage_products
):
    # given
    # another app - to be sure we don't mix it with app from the app_api_client
    another_app = App.objects.create(
        name="External App",
        is_active=True,
        type=AppType.THIRDPARTY,
        identifier="mirumee.app.sample",
        about_app="About app text.",
        data_privacy="Data privacy text.",
        data_privacy_url="http://www.example.com/privacy/",
        homepage_url="http://www.example.com/homepage/",
        support_url="http://www.example.com/support/contact/",
        configuration_url="http://www.example.com/app-configuration/",
        app_url="http://www.example.com/app/",
    )

    app_extension = AppExtension.objects.create(
        app=another_app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_EXTENSION_WITH_APP,
        variables,
    )

    # then
    # Can't access other apps
    assert_no_permission(response)


def test_app_extension_with_app_query_by_owner_app(
    app, app_api_client, permission_manage_products
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_EXTENSION_WITH_APP,
        variables,
    )

    # then
    get_graphql_content(response)


def test_app_extension_with_app_query_by_staff_with_permissions(
    external_app, app, staff_api_client, permission_group_manage_apps
):
    # given
    app_extension = AppExtension.objects.create(
        app=external_app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )

    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    staff_api_client.user.groups.add(permission_group_manage_apps)

    # when
    response = staff_api_client.post_graphql(QUERY_APP_EXTENSION_WITH_APP, variables)

    # then
    response = get_graphql_content(response)

    assert response["data"]["appExtension"]["id"] == id


def test_app_extension_with_app_query_by_customer_without_permissions(
    external_app, app, api_client, permission_group_manage_apps
):
    # given
    app_extension = AppExtension.objects.create(
        app=external_app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )

    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = api_client.post_graphql(QUERY_APP_EXTENSION_WITH_APP, variables)

    # then
    assert_no_permission(response)


@pytest.mark.parametrize(
    ("target", "method"),
    [
        (AppExtensionTarget.WIDGET, "POST"),
        (AppExtensionTarget.WIDGET, "GET"),
        (AppExtensionTarget.NEW_TAB, "POST"),
        (AppExtensionTarget.NEW_TAB, "GET"),
    ],
)
def test_app_extension_type_options(
    target,
    method,
    app,
    staff_api_client,
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.ORDER_DETAILS_WIDGETS,
        http_target_method=method,
        target=target,
    )
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]

    assert extension_data["target"] == target.upper()

    assert extension_data["mountName"] == "ORDER_DETAILS_WIDGETS"
    assert extension_data["targetName"] == app_extension.target.upper()

    if target == AppExtensionTarget.NEW_TAB:
        assert extension_data["options"]["newTabTarget"]["method"] == method
        assert extension_data["settings"]["newTabTarget"]["method"] == method

    if target == AppExtensionTarget.WIDGET:
        assert extension_data["options"]["widgetTarget"]["method"] == method
        assert extension_data["settings"]["widgetTarget"]["method"] == method


@pytest.mark.parametrize(
    ("base_target", "use_uppercase", "method"),
    [
        (AppExtensionTarget.WIDGET, False, "POST"),
        (AppExtensionTarget.WIDGET, True, "POST"),
        (AppExtensionTarget.NEW_TAB, False, "GET"),
        (AppExtensionTarget.NEW_TAB, True, "GET"),
    ],
)
def test_app_extension_resolve_options_with_case_variations(
    base_target,
    use_uppercase,
    method,
    app,
    staff_api_client,
):
    """Test that resolve_options works with both uppercase and lowercase target values.

    This is important for zero-downtime migrations where the target field
    transitions from lowercase enum values to uppercase string values.
    """
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
        http_target_method=method,
        target=base_target,
    )

    # Simulate migration by updating to uppercase value directly in DB
    if use_uppercase:
        AppExtension.objects.filter(pk=app_extension.pk).update(
            target=base_target.upper()
        )
        app_extension.refresh_from_db()

    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]

    # Check that options are resolved correctly regardless of case
    if base_target.upper() == AppExtensionTarget.WIDGET.upper():
        assert extension_data["options"]["widgetTarget"]["method"] == method
    elif base_target.upper() == AppExtensionTarget.NEW_TAB.upper():
        assert extension_data["options"]["newTabTarget"]["method"] == method


@pytest.mark.parametrize(
    ("base_target", "use_uppercase", "method"),
    [
        (AppExtensionTarget.WIDGET, False, "POST"),
        (AppExtensionTarget.WIDGET, True, "POST"),
        (AppExtensionTarget.NEW_TAB, False, "GET"),
        (AppExtensionTarget.NEW_TAB, True, "GET"),
    ],
)
def test_app_extension_resolve_settings_with_case_variations(
    base_target,
    use_uppercase,
    method,
    app,
    staff_api_client,
):
    """Test that resolve_settings works with both uppercase and lowercase target values.

    This is important for zero-downtime migrations where the target field
    transitions from lowercase enum values to uppercase string values.
    """
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
        http_target_method=method,
        target=base_target,
    )

    # Simulate migration by updating to uppercase value directly in DB
    if use_uppercase:
        AppExtension.objects.filter(pk=app_extension.pk).update(
            target=base_target.upper()
        )
        app_extension.refresh_from_db()

    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]

    # Check that settings are resolved correctly regardless of case
    if base_target.upper() == AppExtensionTarget.WIDGET.upper():
        assert extension_data["settings"]["widgetTarget"]["method"] == method
    elif base_target.upper() == AppExtensionTarget.NEW_TAB.upper():
        assert extension_data["settings"]["newTabTarget"]["method"] == method


@pytest.mark.parametrize(
    ("base_mount", "base_target", "use_uppercase"),
    [
        # lowercase values (current DB state before migration)
        (
            AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
            AppExtensionTarget.POPUP,
            False,
        ),
        (AppExtensionMount.ORDER_DETAILS_WIDGETS, AppExtensionTarget.WIDGET, False),
        # uppercase values (after migration)
        (
            AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
            AppExtensionTarget.POPUP,
            True,
        ),
        (AppExtensionMount.ORDER_DETAILS_WIDGETS, AppExtensionTarget.WIDGET, True),
    ],
)
def test_app_extension_resolve_mount_name_and_target_name_with_case_variations(
    base_mount,
    base_target,
    use_uppercase,
    app,
    staff_api_client,
):
    """Test that resolve_mount_name and resolve_target_name work with both cases.

    This is important for zero-downtime migrations where mount and target fields
    transition from lowercase enum values to uppercase string values.
    """
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=base_mount,
        target=base_target,
        http_target_method="POST",
    )

    # Simulate migration by updating to uppercase values directly in DB
    if use_uppercase:
        AppExtension.objects.filter(pk=app_extension.pk).update(
            mount=base_mount.upper(), target=base_target.upper()
        )
        app_extension.refresh_from_db()

    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]

    # Both mountName and targetName should always return uppercase values
    assert extension_data["mountName"] == base_mount.upper()
    assert extension_data["targetName"] == base_target.upper()
