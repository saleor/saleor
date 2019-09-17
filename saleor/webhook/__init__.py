from django.utils.translation import pgettext_lazy


class WebhookEventType:
    ORDER_CREATED = "order_created"
    CUSTOMER_CREATED = "customer_created"

    CHOICES = [
        (ORDER_CREATED, pgettext_lazy("Order has been placed", "Order created")),
        (
            CUSTOMER_CREATED,
            pgettext_lazy("Customer has been created", "Customer created"),
        ),
    ]
    PERMISSIONS = {
        ORDER_CREATED: "order.manage_orders",
        CUSTOMER_CREATED: "account.manage_users",
    }
