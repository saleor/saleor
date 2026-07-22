from unittest.mock import patch

from ......account.error_codes import CustomerTypeCreateErrorCode
from ......account.models import CustomerType
from .....tests.utils import assert_no_permission, get_graphql_content

CUSTOMER_TYPE_CREATE_MUTATION = """
    mutation CustomerTypeCreate($input: CustomerTypeCreateInput!) {
        customerTypeCreate(input: $input) {
            customerType {
                id
                name
                slug
                isDefault
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_create_by_staff_with_permission(
    staff_api_client, permission_manage_customer_types_and_attributes
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    name = "Wholesale"
    variables = {"input": {"name": name}}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeCreate"]
    assert data["errors"] == []

    customer_type = CustomerType.objects.get(slug="wholesale")
    assert data["customerType"]["name"] == customer_type.name
    assert data["customerType"]["slug"] == customer_type.slug
    assert data["customerType"]["isDefault"] is False
    assert customer_type.name == name
    assert customer_type.is_default is False


def test_create_with_explicit_slug(
    staff_api_client, permission_manage_customer_types_and_attributes
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    name = "Wholesale"
    slug = "custom-slug"
    variables = {"input": {"name": name, "slug": slug}}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeCreate"]
    assert data["errors"] == []

    customer_type = CustomerType.objects.get(slug=slug)
    assert customer_type.name == name
    assert data["customerType"]["slug"] == slug


def test_create_as_default_transfers_default_flag(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    default_customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {"input": {"name": "Wholesale", "isDefault": True}}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeCreate"]
    assert data["errors"] == []
    assert data["customerType"]["isDefault"] is True

    default_customer_type.refresh_from_db()
    assert default_customer_type.is_default is False

    customer_type = CustomerType.objects.get(slug="wholesale")
    assert customer_type.is_default is True
    assert CustomerType.objects.filter(is_default=True).count() == 1


def test_create_with_duplicated_slug(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {"input": {"name": "Another", "slug": customer_type.slug}}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeCreate"]
    assert data["customerType"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "slug"
    assert error["code"] == CustomerTypeCreateErrorCode.UNIQUE.name


def test_create_without_name(
    staff_api_client, permission_manage_customer_types_and_attributes
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {"input": {}}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeCreate"]
    assert data["customerType"] is None
    assert len(data["errors"]) == 2
    errors_by_field = {error["field"]: error for error in data["errors"]}
    assert errors_by_field.keys() == {"name", "slug"}
    assert errors_by_field["name"]["code"] == CustomerTypeCreateErrorCode.REQUIRED.name
    assert errors_by_field["slug"]["code"] == CustomerTypeCreateErrorCode.REQUIRED.name


def test_create_by_staff_without_permission(staff_api_client):
    # given
    variables = {"input": {"name": "Wholesale"}}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_CREATE_MUTATION, variables)

    # then
    assert_no_permission(response)
    assert not CustomerType.objects.filter(slug="wholesale").exists()


@patch("saleor.plugins.manager.PluginsManager.customer_type_created")
def test_create_triggers_webhook(
    mocked_customer_type_created,
    staff_api_client,
    permission_manage_customer_types_and_attributes,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {"input": {"name": "Wholesale"}}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["customerTypeCreate"]["errors"] == []

    customer_type = CustomerType.objects.get(slug="wholesale")
    mocked_customer_type_created.assert_called_once_with(customer_type)
