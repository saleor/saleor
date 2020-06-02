from enum import Enum
from unittest.mock import Mock

import graphene
import pytest
from django.core.exceptions import ImproperlyConfigured

from saleor.graphql.core.mutations import BaseMutation
from saleor.graphql.core.types.common import Error
from saleor.graphql.product import types as product_types


class Mutation(BaseMutation):
    name = graphene.Field(graphene.String)

    class Arguments:
        product_id = graphene.ID(required=True)

    class Meta:
        description = "Base mutation"

    @classmethod
    def perform_mutation(cls, _root, info, product_id):
        product = cls.get_node_or_error(
            info, product_id, field="product_id", only_type=product_types.Product
        )
        return Mutation(name=product.name)


class ErrorCodeTest(Enum):
    INVALID = "invalid"


ErrorCodeTest = graphene.Enum.from_enum(ErrorCodeTest)


class ErrorTest(Error):
    code = ErrorCodeTest()


class MutationWithCustomErrors(Mutation):
    class Meta:
        description = "Base mutation with custom errors"
        error_type_class = ErrorTest
        error_type_field = "custom_errors"


class Mutations(graphene.ObjectType):
    test = Mutation.Field()
    test_with_custom_errors = MutationWithCustomErrors.Field()


schema = graphene.Schema(
    mutation=Mutations, types=[product_types.Product, product_types.ProductVariant]
)


def test_mutation_without_description_raises_error():
    with pytest.raises(ImproperlyConfigured):

        class MutationNoDescription(BaseMutation):
            name = graphene.Field(graphene.String)

            class Arguments:
                product_id = graphene.ID(required=True)


def test_resolve_id(product, schema_context):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    query = """
        mutation testMutation($productId: ID!) {
            test(productId: $productId) {
                name
                errors {
                    field
                    message
                }
            }
        }
    """
    variables = {"productId": product_id}
    result = schema.execute(query, variables=variables, context_value=schema_context)
    assert not result.errors
    assert result.data["test"]["name"] == product.name


def test_user_error_nonexistent_id(schema_context):
    query = """
        mutation testMutation($productId: ID!) {
            test(productId: $productId) {
                name
                errors {
                    field
                    message
                }
            }
        }
    """
    variables = {"productId": "not-really"}
    result = schema.execute(query, variables=variables, context_value=schema_context)
    assert not result.errors
    user_errors = result.data["test"]["errors"]
    assert user_errors
    assert user_errors[0]["field"] == "productId"
    assert user_errors[0]["message"] == "Couldn't resolve to a node: not-really"


def test_mutation_custom_errors_default_value(product, schema_context):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    query = """
        mutation testMutation($productId: ID!) {
            testWithCustomErrors(productId: $productId) {
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
    variables = {"productId": product_id}
    result = schema.execute(query, variables=variables, context_value=schema_context)
    assert result.data["testWithCustomErrors"]["errors"] == []
    assert result.data["testWithCustomErrors"]["customErrors"] == []


def test_user_error_id_of_different_type(product, schema_context):
    query = """
        mutation testMutation($productId: ID!) {
            test(productId: $productId) {
                name
                errors {
                    field
                    message
                }
            }
        }
    """

    # Test that get_node_or_error checks that the returned ID must be of
    # proper type. Providing correct ID but of different type than expected
    # should result in user error.
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {"productId": variant_id}
    result = schema.execute(query, variables=variables, context_value=schema_context)
    assert not result.errors
    user_errors = result.data["test"]["errors"]
    assert user_errors
    assert user_errors[0]["field"] == "productId"
    assert user_errors[0]["message"] == "Must receive a Product id"


def test_get_node_or_error_returns_null_for_empty_id():
    info = Mock()
    response = Mutation.get_node_or_error(info, "", field="")
    assert response is None
