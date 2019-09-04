import graphene

from ...core.mutations import BaseMutation, ModelMutation
from ...core.types.common import ProductError


class ProductErrorMixin:
    product_errors = graphene.List(
        graphene.NonNull(ProductError),
        description="List of errors that occurred executing the mutation.",
    )
    ERROR_TYPE_CLASS = ProductError
    ERROR_TYPE_FIELD = "product_errors"


class BaseProductMutation(ProductErrorMixin, BaseMutation):
    class Meta:
        abstract = True


class ModelProductMutation(ProductErrorMixin, ModelMutation):
    class Meta:
        abstract = True
