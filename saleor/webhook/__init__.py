from django.utils.translation import pgettext_lazy


class WebhookEventType:
    ALL = "all_events"
    ORDER_CREATED = "order_created"
    ORDER_FULLYPAID = "order_fully_paid"
    ORDER_UPDATED = "order_updated"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_FULFILLED = "order_fulfilled"

    CUSTOMER_CREATED = "customer_created"

    PRODUCT_CREATED = "product_created"

    CHOICES = [
        (ALL, pgettext_lazy("All events", "All events")),
        (ORDER_CREATED, pgettext_lazy("Order has been placed", "Order created")),
        (ORDER_FULLYPAID, pgettext_lazy("Order has been fully paid", "Order paid")),
        (ORDER_UPDATED, pgettext_lazy("Order has been updated", "Order updated")),
        (ORDER_CANCELLED, pgettext_lazy("Order has been cancelled", "Order cancelled")),
        (
            CUSTOMER_CREATED,
            pgettext_lazy("Customer has been created", "Customer created"),
        ),
        (PRODUCT_CREATED, pgettext_lazy("Product has been created", "Product created")),
    ]
    PERMISSIONS = {
        ORDER_CREATED: "order.manage_orders",
        ORDER_FULLYPAID: "order.manage_orders",
        CUSTOMER_CREATED: "account.manage_users",
        PRODUCT_CREATED: "product.manage_products",
    }
