import graphene
from django.db.models import CharField, ExpressionWrapper, OuterRef, QuerySet, Subquery

from ...payment.models import Payment
from ..core.types import SortInputObjectType


class OrderSortField(graphene.Enum):
    NUMBER = ["pk"]
    CREATION_DATE = ["created", "status", "pk"]
    CUSTOMER = ["billing_address__last_name", "billing_address__first_name", "pk"]
    PAYMENT = ["last_charge_status", "status", "pk"]
    FULFILLMENT_STATUS = ["status", "user_email", "pk"]
    TOTAL = ["total_gross_amount", "status", "pk"]

    @property
    def description(self):
        if self.name in OrderSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort orders by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_payment(queryset: QuerySet) -> QuerySet:
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
