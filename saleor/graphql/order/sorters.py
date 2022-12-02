import graphene
from django.db.models import CharField, ExpressionWrapper, OuterRef, QuerySet, Subquery

from ...payment.models import Payment
from ..core.descriptions import DEPRECATED_IN_3X_INPUT
from ..core.types import SortInputObjectType


class OrderSortField(graphene.Enum):
    NUMBER = ["number"]
    RANK = ["search_rank", "id"]
    CREATION_DATE = ["created_at", "status", "pk"]
    CREATED_AT = ["created_at", "status", "pk"]
    LAST_MODIFIED_AT = ["updated_at", "status", "pk"]
    CUSTOMER = ["billing_address__last_name", "billing_address__first_name", "pk"]
    PAYMENT = ["last_charge_status", "status", "pk"]
    FULFILLMENT_STATUS = ["status", "user_email", "pk"]

    @property
    def description(self):
        descriptions = {
            OrderSortField.RANK.name: (
                "rank. Note: This option is available only with the `search` filter."
            ),
            OrderSortField.CREATION_DATE.name: (
                f"creation date. {DEPRECATED_IN_3X_INPUT}"
            ),
        }

        if self.name in OrderSortField.__enum__._member_names_:
            if self.name in descriptions:
                return f"Sort orders by {descriptions[self.name]}"

            sort_name = self.name.lower().replace("_", " ")
            return f"Sort orders by {sort_name}."

        raise ValueError("Unsupported enum value: %s" % self.value)

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
        sort_enum = OrderSortField
        type_name = "orders"
