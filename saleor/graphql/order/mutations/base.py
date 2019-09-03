import graphene

from ...core.mutations import BaseMutation
from ...core.types.common import OrderError


class OrderErrorMixin:
    order_errors = graphene.List(
        graphene.NonNull(OrderError),
        description="List of errors that occurred executing the mutation.",
    )

    @classmethod
    def handle_typed_errors(cls, errors: list, **extra):
        order_errors = [
            OrderError(field=e.field, message=e.message, code=code)
            for e, code in errors
        ]
        return cls(errors=[e[0] for e in errors], order_errors=order_errors, **extra)


class BaseOrderMutation(OrderErrorMixin, BaseMutation):
    class Meta:
        abstract = True
