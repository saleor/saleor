import graphene
import pytest
from django.core.exceptions import ImproperlyConfigured

from saleor.graphql.core.mutations import BaseMutation
from saleor.graphql.product import types as product_types


class Mutation(BaseMutation):
    name = graphene.Field(graphene.String)

    class Arguments:
        product_id = graphene.ID(required=True)

    class Meta:
        description = 'Base mutation'

    @classmethod
    def mutate(cls, root, info, product_id):
        errors = []
        product = cls.get_node_or_error(
            info, product_id, errors, 'product_id', product_types.Product)
        if errors:
            return Mutation(errors=errors)
        return Mutation(name=product.name)


class Mutations(graphene.ObjectType):
    test = Mutation.Field()


schema = graphene.Schema(
    mutation=Mutations,
    types=[product_types.Product, product_types.ProductVariant])


def test_mutation_without_description_raises_error():
    with pytest.raises(ImproperlyConfigured) as exc_info:
        class MutationNoDescription(BaseMutation):
            name = graphene.Field(graphene.String)

            class Arguments:
                product_id = graphene.ID(required=True)


def test_resolve_id(product):
    product_id = graphene.Node.to_global_id('Product', product.pk)
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
    variables = {'productId': product_id}
    result = schema.execute(query, variables=variables)
    assert not result.errors
    assert result.data['test']['name'] == product.name


def test_user_error_nonexistent_id():
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
    variables = {'productId': 'not-really'}
    result = schema.execute(query, variables=variables)
    assert not result.errors
    user_errors = result.data['test']['errors']
    assert user_errors
    assert user_errors[0]['field'] == 'productId'
    assert "Couldn't resolve to a node" in user_errors[0]['message']


def test_user_error_id_of_different_type(product):
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
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)

    variables = {'productId': variant_id}
    result = schema.execute(query, variables=variables)
    assert not result.errors
    user_errors = result.data['test']['errors']
    assert user_errors
    assert user_errors[0]['field'] == 'productId'
    assert user_errors[0]['message'] == 'Must receive a Product id.'
