import graphene

from ...core.mutations import BaseMutation
from ...core.types.common import OrderError


class OrderErrorMixin:
    order_errors = graphene.List(
        graphene.NonNull(OrderError),
        description="List of errors that occurred executing the mutation.",
    )

    ERROR_TYPE_CLASS = OrderError
    ERROR_TYPE_FIELD = "order_errors"


class BaseOrderMutation(OrderErrorMixin, BaseMutation):
    class Meta:
        abstract = True
