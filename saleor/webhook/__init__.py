from django.utils.translation import pgettext_lazy


class WebhookEventType:
    ANY = "any_events"
    ORDER_CREATED = "order_created"
    ORDER_FULLY_PAID = "order_fully_paid"
    ORDER_UPDATED = "order_updated"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_FULFILLED = "order_fulfilled"

    CUSTOMER_CREATED = "customer_created"

    PRODUCT_CREATED = "product_created"

    CHOICES = [
        (ANY, pgettext_lazy("Any events", "Any events")),
        (ORDER_CREATED, pgettext_lazy("Order has been placed", "Order created")),
        (ORDER_FULLY_PAID, pgettext_lazy("Order has been fully paid", "Order paid")),
        (ORDER_UPDATED, pgettext_lazy("Order has been updated", "Order updated")),
        (ORDER_CANCELLED, pgettext_lazy("Order has been cancelled", "Order cancelled")),
        (ORDER_FULFILLED, pgettext_lazy("Order has been fulfilled", "Order fulfilled")),
        (
            CUSTOMER_CREATED,
            pgettext_lazy("Customer has been created", "Customer created"),
        ),
        (PRODUCT_CREATED, pgettext_lazy("Product has been created", "Product created")),
    ]
    PERMISSIONS = {
        ORDER_CREATED: "order.manage_orders",
        ORDER_FULLY_PAID: "order.manage_orders",
        ORDER_UPDATED: "order.manage_orders",
        ORDER_CANCELLED: "order.manage_orders",
        ORDER_FULFILLED: "order.manage_orders",
        CUSTOMER_CREATED: "account.manage_users",
        PRODUCT_CREATED: "product.manage_products",
    }
