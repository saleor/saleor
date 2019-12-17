import graphene
from django.db.models import FilteredRelation, Max, Q, QuerySet

from ..core.types import SortInputObjectType


class OrderSortField(graphene.Enum):
    NUMBER = "pk"
    CREATION_DATE = "created"
    CUSTOMER = "customer"
    PAYMENT = "payment"
    FULFILLMENT_STATUS = "status"
    TOTAL = "total_gross_amount"

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            OrderSortField.NAME,
            OrderSortField.CREATION_DATE,
            OrderSortField.CUSTOMER,
            OrderSortField.PAYMENT,
            OrderSortField.FULFILLMENT_STATUS,
            OrderSortField.TOTAL,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort orders by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def sort_by_customer(queryset: QuerySet, sort_by: SortInputObjectType) -> QuerySet:
        return queryset.order_by(
            f"{sort_by.direction}billing_address__first_name",
            f"{sort_by.direction}billing_address__last_name",
        )

    @staticmethod
    def sort_by_payment(queryset: QuerySet, sort_by: SortInputObjectType) -> QuerySet:
        last_payments = (
            queryset.exclude(payments__isnull=True)
            .annotate(payment_id=Max("payments__pk"))
            .values_list("payment_id", flat=True)
        )
        queryset = queryset.annotate(
            last_payment=FilteredRelation(
                "payments", condition=Q(payments__pk__in=last_payments)
            )
        )
        return queryset.order_by(f"{sort_by.direction}last_payment__charge_status")


class OrderSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = OrderSortField
        type_name = "orders"
