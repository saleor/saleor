from django.utils.translation import pgettext_lazy


class WebhookEventType:
    ORDER_CREATED = "order_created"

    CHOICES = [(ORDER_CREATED, pgettext_lazy("Order has been placed", "Order created"))]
    PERMISSIONS = {ORDER_CREATED: "order.manage_orders"}
