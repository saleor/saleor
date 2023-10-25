from unittest import mock

import graphene
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time
from graphql import GraphQLError
from graphql.execution import ExecutionResult

from ....core.jwt import create_access_token
from ....graphql.tests.utils import get_graphql_content
from ....order.models import Order
from ....permission.enums import ProductPermissions
from ....plugins.tests.sample_plugins import PluginSample
from ....product.models import Product
from ...order import types as order_types
from ...product import types as product_types
from ..mutations import BaseMutation
from . import ErrorTest


class Mutation(BaseMutation):
    name = graphene.Field(graphene.String)

    class Arguments:
        product_id = graphene.ID(required=True)
        channel = graphene.String()

    class Meta:
        description = "Base mutation"
        error_type_class = ErrorTest

    @classmethod
    def perform_mutation(cls, _root, info, product_id, channel):
        # Need to mock `app_middleware`
        info.context.auth_token = None

        product = cls.get_node_or_error(
            info, product_id, field="product_id", only_type=product_types.Product
        )
        return Mutation(name=product.name)


class MutationWithCustomErrors(Mutation):
    class Meta:
        description = "Base mutation with custom errors"
        error_type_class = ErrorTest
        error_type_field = "custom_errors"


class RestrictedMutation(Mutation):
    """A mutation requiring the user to have certain permissions."""

    auth_token = graphene.types.String(
        description="The newly created authentication token."
    )

    class Meta:
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        description = "Mutation requiring manage product user permission"
        error_type_class = ErrorTest


class OrderMutation(BaseMutation):
    number = graphene.Field(graphene.String)

    class Arguments:
        id = graphene.ID(required=True)
        channel = graphene.String()

    class Meta:
        description = "Base mutation"
        error_type_class = ErrorTest

    @classmethod
    def perform_mutation(cls, _root, info, id, channel):
        # Need to mock `app_middleware`
        info.context.auth_token = None

        order = cls.get_node_or_error(info, id, only_type=order_types.Order)
        return OrderMutation(number=order.number)


class Mutations(graphene.ObjectType):
    test = Mutation.Field()
    test_with_custom_errors = MutationWithCustomErrors.Field()
    restricted_mutation = RestrictedMutation.Field()
    test_order_mutation = OrderMutation.Field()


schema = graphene.Schema(
    mutation=Mutations,
    types=[product_types.Product, product_types.ProductVariant, order_types.Order],
)


def test_mutation_without_description_raises_error():
    with pytest.raises(ImproperlyConfigured):

        class MutationNoDescription(BaseMutation):
            name = graphene.Field(graphene.String)

            class Arguments:
                product_id = graphene.ID(required=True)


def test_mutation_without_error_type_class_raises_error():
    with pytest.raises(ImproperlyConfigured):

        class MutationNoDescription(BaseMutation):
            name = graphene.Field(graphene.String)
            description = "Base mutation with custom errors"

            class Arguments:
                product_id = graphene.ID(required=True)


TEST_MUTATION = """
    mutation testMutation($productId: ID!, $channel: String) {
        test(productId: $productId, channel: $channel) {
            name
            errors {
                field
                message
            }
        }
    }
"""


def test_resolve_id(product, schema_context, channel_USD):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {"productId": product_id, "channel": channel_USD.slug}
    result = schema.execute(
        TEST_MUTATION, variables=variables, context_value=schema_context
    )
    assert not result.errors
    assert result.data["test"]["name"] == product.name


def test_user_error_nonexistent_id(schema_context, channel_USD):
    variables = {"productId": "not-really", "channel": channel_USD.slug}
    result = schema.execute(
        TEST_MUTATION, variables=variables, context_value=schema_context
    )
    assert not result.errors
    user_errors = result.data["test"]["errors"]
    assert user_errors
    assert user_errors[0]["field"] == "productId"
    assert user_errors[0]["message"] == "Invalid ID: not-really. Expected: Product."


TEST_ORDER_MUTATION = """
    mutation TestOrderMutation($id: ID!, $channel: String) {
        testOrderMutation(id: $id, channel: $channel) {
            number
            errors {
                field
                message
            }
        }
    }
"""


def test_order_mutation_resolve_uuid_id(order, schema_context, channel_USD):
    order_id = graphene.Node.to_global_id("Order", order.pk)
    variables = {"id": order_id, "channel": channel_USD.slug}
    result = schema.execute(
        TEST_ORDER_MUTATION, variables=variables, context_value=schema_context
    )
    assert not result.errors
    assert result.data["testOrderMutation"]["number"] == str(order.number)


def test_order_mutation_for_old_int_id(order, schema_context, channel_USD):
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    order_id = graphene.Node.to_global_id("Order", order.number)
    variables = {"id": order_id, "channel": channel_USD.slug}
    result = schema.execute(
        TEST_ORDER_MUTATION, variables=variables, context_value=schema_context
    )
    assert not result.errors
    assert result.data["testOrderMutation"]["number"] == str(order.number)


def test_mutation_custom_errors_default_value(product, schema_context, channel_USD):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    query = """
        mutation testMutation($productId: ID!, $channel: String) {
            testWithCustomErrors(productId: $productId, channel: $channel) {
                name
                errors {
                    field
                    message
                }
                customErrors {
                    field
                    message
                }
            }
        }
    """
    variables = {"productId": product_id, "channel": channel_USD.slug}
    result = schema.execute(query, variables=variables, context_value=schema_context)
    assert result.data["testWithCustomErrors"]["errors"] == []
    assert result.data["testWithCustomErrors"]["customErrors"] == []


def test_user_error_id_of_different_type(product, schema_context, channel_USD):
    # Test that get_node_or_error checks that the returned ID must be of
    # proper type. Providing correct ID but of different type than expected
    # should result in user error.
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {"productId": variant_id, "channel": channel_USD.slug}
    result = schema.execute(
        TEST_MUTATION, variables=variables, context_value=schema_context
    )
    assert not result.errors
    user_errors = result.data["test"]["errors"]
    assert user_errors
    assert user_errors[0]["field"] == "productId"
    assert (
        user_errors[0]["message"]
        == f"Invalid ID: {variant_id}. Expected: Product, received: ProductVariant."
    )


def test_get_node_or_error_returns_null_for_empty_id():
    info = mock.Mock()
    response = Mutation.get_node_or_error(info, "", field="")
    assert response is None


def test_mutation_plugin_perform_mutation_handles_graphql_error(
    request,
    settings,
    plugin_configuration,
    product,
    channel_USD,
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]

    schema_context = request.getfixturevalue("schema_context")

    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {"productId": product_id, "channel": channel_USD.slug}

    with mock.patch.object(
        PluginSample,
        "perform_mutation",
        return_value=GraphQLError("My Custom Error"),
    ):
        result = schema.execute(
            TEST_MUTATION, variables=variables, context_value=schema_context
        )
    assert result.to_dict() == {
        "data": {"test": None},
        "errors": [
            {
                "locations": [{"column": 9, "line": 3}],
                "message": "My Custom Error",
                "path": ["test"],
            }
        ],
    }


def test_mutation_plugin_perform_mutation_handles_custom_execution_result(
    request,
    settings,
    plugin_configuration,
    product,
    channel_USD,
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]

    schema_context = request.getfixturevalue("schema_context")

    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {"productId": product_id, "channel": channel_USD.slug}

    with mock.patch.object(
        PluginSample,
        "perform_mutation",
        return_value=ExecutionResult(data={}, errors=[GraphQLError("My Custom Error")]),
    ):
        result = schema.execute(
            TEST_MUTATION, variables=variables, context_value=schema_context
        )
    assert result.to_dict() == {
        "data": {"test": None},
        "errors": [
            {
                "locations": [{"column": 13, "line": 5}],
                "message": "My Custom Error",
                "path": ["test", "errors", 0],
            }
        ],
    }


@mock.patch.object(
    PluginSample,
    "perform_mutation",
    return_value=ExecutionResult(data={}, errors=[GraphQLError("My Custom Error")]),
)
def test_mutation_calls_plugin_perform_mutation_after_permission_checks(
    mocked_plugin,
    request,
    settings,
    staff_user,
    plugin_configuration,
    product,
    channel_USD,
    permission_manage_products,
):
    mutation_query = """
        mutation testRestrictedMutation($productId: ID!, $channel: String) {
            restrictedMutation(productId: $productId, channel: $channel) {
                name
                errors {
                    field
                    message
                }
            }
        }
    """

    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]

    schema_context = request.getfixturevalue("schema_context")
    schema_context.user = SimpleLazyObject(lambda: staff_user)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {"productId": product_id, "channel": channel_USD.slug}

    # When permission is missing, it should not return the custom error from plugin
    result = schema.execute(
        mutation_query, variables=variables, context_value=schema_context
    )
    assert len(result.errors) == 1, result.to_dict()
    assert (
        "To access this path, you need one of the following permissions"
        in result.errors[0].message
    )

    # When permission is not missing, the execution of the plugin should happen
    staff_user.user_permissions.set([permission_manage_products])
    del staff_user._perm_cache  # force django to re-fetch permissions
    result = schema.execute(
        mutation_query, variables=variables, context_value=schema_context
    )
    assert len(result.errors) == 1, result.to_dict()
    assert result.errors[0].message == "My Custom Error"


def test_base_mutation_get_node_by_pk_with_order_qs_and_old_int_id(order):
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    # when
    node = BaseMutation._get_node_by_pk(
        None, order_types.Order, order.number, qs=Order.objects.all()
    )

    # then
    assert node.id == order.id


def test_base_mutation_get_node_by_pk_with_order_qs_and_new_uuid_id(order):
    # when
    node = BaseMutation._get_node_by_pk(
        None, order_types.Order, order.pk, qs=Order.objects.all()
    )

    # then
    assert node.id == order.id


def test_base_mutation_get_node_by_pk_with_order_qs_and_int_id_use_old_id_set_to_false(
    order,
):
    # given
    order.use_old_id = False
    order.save(update_fields=["use_old_id"])

    # when
    node = BaseMutation._get_node_by_pk(
        None, order_types.Order, order.number, qs=Order.objects.all()
    )

    # then
    assert node is None


def test_base_mutation_get_node_by_pk_with_qs_for_product(product):
    # when
    node = BaseMutation._get_node_by_pk(
        None, product_types.Product, product.pk, qs=Product.objects.all()
    )

    # then
    assert node.id == product.id


def test_expired_token_error(user_api_client, channel_USD):
    # given
    user = user_api_client.user
    with freeze_time("2023-01-01 12:00:00"):
        expired_access_token = create_access_token(user)
        user_api_client.token = expired_access_token

    mutation = """
      mutation createCheckout($checkoutInput: CheckoutCreateInput!) {
        checkoutCreate(input: $checkoutInput) {
          checkout {
            id
          }
          errors {
            field
            message
            code
          }
        }
      }
    """

    # when
    variables = {"checkoutInput": {"channel": channel_USD.slug, "lines": []}}
    response = user_api_client.post_graphql(mutation, variables)
    content = get_graphql_content(response, ignore_errors=True)

    # then
    error = content["errors"][0]
    assert error["message"] == "Signature has expired"
    assert error["extensions"]["exception"]["code"] == "ExpiredSignatureError"
