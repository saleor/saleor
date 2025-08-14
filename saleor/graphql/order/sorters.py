from django.db.models import CharField, ExpressionWrapper, OuterRef, QuerySet, Subquery

from ...payment.models import Payment
from ..core.descriptions import ADDED_IN_322
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.types import BaseEnum, SortInputObjectType


class OrderSortField(BaseEnum):
    NUMBER = ["number"]
    RANK = ["search_rank", "id"]
    CREATION_DATE = ["created_at", "status", "number", "pk"]
    CREATED_AT = ["created_at", "status", "number"]
    LAST_MODIFIED_AT = ["updated_at", "status", "number"]
    CUSTOMER = ["billing_address__last_name", "billing_address__first_name", "number"]
    PAYMENT = ["last_charge_status", "status", "number"]
    FULFILLMENT_STATUS = ["status", "user_email", "number"]
    STATUS = ["status", "number"]

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS

    @property
    def description(self):
        descriptions = {
            OrderSortField.NUMBER.name: "number.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            OrderSortField.RANK.name: (  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
                "rank. Note: This option is available only with the `search` filter."
            ),
            OrderSortField.CREATION_DATE.name: "creation date",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            OrderSortField.CREATED_AT.name: "creation date.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            OrderSortField.LAST_MODIFIED_AT.name: "last modified date.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            OrderSortField.CUSTOMER.name: "customer.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            OrderSortField.PAYMENT.name: "payment status.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            OrderSortField.FULFILLMENT_STATUS.name: "fulfillment status.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            OrderSortField.STATUS.name: f"order status. {ADDED_IN_322}",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
        }
        if self.name in descriptions:
            return f"Sort orders by {descriptions[self.name]}"
        raise ValueError(f"Unsupported enum value: {self.value}")

    @property
    def deprecation_reason(self):
        deprecations = {
            OrderSortField.CREATION_DATE.name: "Use `CREATED_AT` instead.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            OrderSortField.FULFILLMENT_STATUS.name: "Use `STATUS` instead.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
        }
        if self.name in deprecations:
            return deprecations[self.name]
        return None

    @staticmethod
    def qs_with_payment(queryset: QuerySet, **_kwargs) -> QuerySet:
        subquery = Subquery(
            Payment.objects.filter(order_id=OuterRef("pk"))
            .order_by("-pk")
            .values_list("charge_status")[:1]
        )
        return queryset.annotate(
            last_charge_status=ExpressionWrapper(subquery, output_field=CharField())
        )


class OrderSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        sort_enum = OrderSortField
        type_name = "orders"
