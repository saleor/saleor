from django.db.models import CharField, ExpressionWrapper, OuterRef, QuerySet, Subquery

from ...payment.models import Payment
from ..core.descriptions import ADDED_IN_322, DEPRECATED_IN_3X_INPUT
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.types import BaseEnum, SortInputObjectType


class OrderSortField(BaseEnum):
    NUMBER = ["number"]
    RANK = ["search_rank", "id"]
    CREATION_DATE = ["created_at", "status", "pk"]
    CREATED_AT = ["created_at", "status", "pk"]
    LAST_MODIFIED_AT = ["updated_at", "status", "pk"]
    CUSTOMER = ["billing_address__last_name", "billing_address__first_name", "pk"]
    PAYMENT = ["last_charge_status", "status", "pk"]
    FULFILLMENT_STATUS = ["status", "user_email", "pk"]
    STATUS = ["status", "pk"]

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS

    @property
    def description(self):
        descriptions = {
            OrderSortField.RANK.name: (  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
                "rank. Note: This option is available only with the `search` filter."
            ),
            OrderSortField.CREATION_DATE.name: (  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
                f"creation date. {DEPRECATED_IN_3X_INPUT}"
            ),
            OrderSortField.STATUS.name: (  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
                f"status. {ADDED_IN_322}"
            ),
        }

        if self.name in OrderSortField.__enum__._member_names_:
            if self.name in descriptions:
                return f"Sort orders by {descriptions[self.name]}"

            sort_name = self.name.lower().replace("_", " ")
            return f"Sort orders by {sort_name}."

        raise ValueError(f"Unsupported enum value: {self.value}")

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
