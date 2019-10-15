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

    DISPLAY_LABELS = {
        ANY: "Any events",
        ORDER_CREATED: "Order created",
        ORDER_FULLY_PAID: "Order paid",
        ORDER_UPDATED: "Order updated",
        ORDER_CANCELLED: "Order cancelled",
        ORDER_FULFILLED: "Order fulfilled",
        CUSTOMER_CREATED: "Customer created",
        PRODUCT_CREATED: "Product created",
    }

    CHOICES = [
        (ANY, pgettext_lazy("Any events", DISPLAY_LABELS[ANY])),
        (
            ORDER_CREATED,
            pgettext_lazy("Order has been placed", DISPLAY_LABELS[ORDER_CREATED]),
        ),
        (
            ORDER_FULLY_PAID,
            pgettext_lazy(
                "Order has been fully paid", DISPLAY_LABELS[ORDER_FULLY_PAID]
            ),
        ),
        (
            ORDER_UPDATED,
            pgettext_lazy("Order has been updated", DISPLAY_LABELS[ORDER_UPDATED]),
        ),
        (
            ORDER_CANCELLED,
            pgettext_lazy("Order has been cancelled", DISPLAY_LABELS[ORDER_CANCELLED]),
        ),
        (
            ORDER_FULFILLED,
            pgettext_lazy("Order has been fulfilled", DISPLAY_LABELS[ORDER_FULFILLED]),
        ),
        (
            CUSTOMER_CREATED,
            pgettext_lazy(
                "Customer has been created", DISPLAY_LABELS[CUSTOMER_CREATED]
            ),
        ),
        (
            PRODUCT_CREATED,
            pgettext_lazy("Product has been created", DISPLAY_LABELS[PRODUCT_CREATED]),
        ),
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
