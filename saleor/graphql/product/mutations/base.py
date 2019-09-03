import graphene

from ...core.mutations import BaseMutation, ModelMutation
from ...core.types.common import ProductError


class ProductErrorMixin:
    product_errors = graphene.List(
        graphene.NonNull(ProductError),
        description="List of errors that occurred executing the mutation.",
    )

    @classmethod
    def handle_typed_errors(cls, errors: list, **extra):
        product_errors = [
            ProductError(field=e.field, message=e.message, code=code)
            for e, code in errors
        ]
        return cls(
            errors=[e[0] for e in errors], product_errors=product_errors, **extra
        )


class BaseProductMutation(ProductErrorMixin, BaseMutation):
    class Meta:
        abstract = True


class ModelProductMutation(ProductErrorMixin, ModelMutation):
    class Meta:
        abstract = True
