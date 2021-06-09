from ..core.permissions import (
    AccountPermissions,
    CheckoutPermissions,
    OrderPermissions,
    PagePermissions,
    PaymentPermissions,
    ProductPermissions,
)


class WebhookEventType:
    ANY = "any_events"
    ORDER_CREATED = "order_created"
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_FULLY_PAID = "order_fully_paid"
    ORDER_UPDATED = "order_updated"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_FULFILLED = "order_fulfilled"

    INVOICE_REQUESTED = "invoice_requested"
    INVOICE_DELETED = "invoice_deleted"
    INVOICE_SENT = "invoice_sent"

    FULFILLMENT_CREATED = "fulfillment_created"

    CUSTOMER_CREATED = "customer_created"
    CUSTOMER_UPDATED = "customer_updated"

    PRODUCT_CREATED = "product_created"
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_DELETED = "product_deleted"

    PRODUCT_VARIANT_CREATED = "product_variant_created"
    PRODUCT_VARIANT_UPDATED = "product_variant_updated"
    PRODUCT_VARIANT_DELETED = "product_variant_deleted"

    CHECKOUT_CREATED = "checkout_created"
    CHECKOUT_UPDATED = "checkout_updated"

    NOTIFY_USER = "notify_user"

    PAGE_CREATED = "page_created"
    PAGE_UPDATED = "page_updated"
    PAGE_DELETED = "page_deleted"

    PAYMENT_LIST_GATEWAYS = "payment_list_gateways"
    PAYMENT_AUTHORIZE = "payment_authorize"
    PAYMENT_CAPTURE = "payment_capture"
    PAYMENT_REFUND = "payment_refund"
    PAYMENT_VOID = "payment_void"
    PAYMENT_CONFIRM = "payment_confirm"
    PAYMENT_PROCESS = "payment_process"

    DISPLAY_LABELS = {
        ANY: "Any events",
        ORDER_CREATED: "Order created",
        ORDER_CONFIRMED: "Order confirmed",
        ORDER_FULLY_PAID: "Order paid",
        ORDER_UPDATED: "Order updated",
        ORDER_CANCELLED: "Order cancelled",
        ORDER_FULFILLED: "Order fulfilled",
        INVOICE_REQUESTED: "Invoice requested",
        INVOICE_DELETED: "Invoice deleted",
        INVOICE_SENT: "Invoice sent",
        CUSTOMER_CREATED: "Customer created",
        CUSTOMER_UPDATED: "Customer updated",
        PRODUCT_CREATED: "Product created",
        PRODUCT_UPDATED: "Product updated",
        PRODUCT_DELETED: "Product deleted",
        PRODUCT_VARIANT_CREATED: "Product variant created",
        PRODUCT_VARIANT_UPDATED: "Product variant updated",
        PRODUCT_VARIANT_DELETED: "Product variant deleted",
        CHECKOUT_CREATED: "Checkout created",
        CHECKOUT_UPDATED: "Checkout updated",
        FULFILLMENT_CREATED: "Fulfillment_created",
        NOTIFY_USER: "Notify user",
        PAGE_CREATED: "Page Created",
        PAGE_UPDATED: "Page Updated",
        PAGE_DELETED: "Page Deleted",
        PAYMENT_AUTHORIZE: "Authorize payment",
        PAYMENT_CAPTURE: "Capture payment",
        PAYMENT_CONFIRM: "Confirm payment",
        PAYMENT_LIST_GATEWAYS: "List payment gateways",
        PAYMENT_PROCESS: "Process payment",
        PAYMENT_REFUND: "Refund payment",
        PAYMENT_VOID: "Void payment",
    }

    CHOICES = [
        (ANY, DISPLAY_LABELS[ANY]),
        (ORDER_CREATED, DISPLAY_LABELS[ORDER_CREATED]),
        (ORDER_CONFIRMED, DISPLAY_LABELS[ORDER_CONFIRMED]),
        (ORDER_FULLY_PAID, DISPLAY_LABELS[ORDER_FULLY_PAID]),
        (ORDER_UPDATED, DISPLAY_LABELS[ORDER_UPDATED]),
        (ORDER_CANCELLED, DISPLAY_LABELS[ORDER_CANCELLED]),
        (ORDER_FULFILLED, DISPLAY_LABELS[ORDER_FULFILLED]),
        (INVOICE_REQUESTED, DISPLAY_LABELS[INVOICE_REQUESTED]),
        (INVOICE_DELETED, DISPLAY_LABELS[INVOICE_DELETED]),
        (INVOICE_SENT, DISPLAY_LABELS[INVOICE_SENT]),
        (CUSTOMER_CREATED, DISPLAY_LABELS[CUSTOMER_CREATED]),
        (CUSTOMER_UPDATED, DISPLAY_LABELS[CUSTOMER_UPDATED]),
        (PRODUCT_CREATED, DISPLAY_LABELS[PRODUCT_CREATED]),
        (PRODUCT_UPDATED, DISPLAY_LABELS[PRODUCT_UPDATED]),
        (PRODUCT_DELETED, DISPLAY_LABELS[PRODUCT_DELETED]),
        (PRODUCT_VARIANT_CREATED, DISPLAY_LABELS[PRODUCT_VARIANT_CREATED]),
        (PRODUCT_VARIANT_UPDATED, DISPLAY_LABELS[PRODUCT_VARIANT_UPDATED]),
        (PRODUCT_VARIANT_DELETED, DISPLAY_LABELS[PRODUCT_VARIANT_DELETED]),
        (CHECKOUT_CREATED, DISPLAY_LABELS[CHECKOUT_CREATED]),
        (CHECKOUT_UPDATED, DISPLAY_LABELS[CHECKOUT_UPDATED]),
        (FULFILLMENT_CREATED, DISPLAY_LABELS[FULFILLMENT_CREATED]),
        (NOTIFY_USER, DISPLAY_LABELS[NOTIFY_USER]),
        (PAGE_CREATED, DISPLAY_LABELS[PAGE_CREATED]),
        (PAGE_UPDATED, DISPLAY_LABELS[PAGE_UPDATED]),
        (PAGE_DELETED, DISPLAY_LABELS[PAGE_DELETED]),
        (PAYMENT_AUTHORIZE, DISPLAY_LABELS[PAYMENT_AUTHORIZE]),
        (PAYMENT_CAPTURE, DISPLAY_LABELS[PAYMENT_CAPTURE]),
        (PAYMENT_CONFIRM, DISPLAY_LABELS[PAYMENT_CONFIRM]),
        (PAYMENT_LIST_GATEWAYS, DISPLAY_LABELS[PAYMENT_LIST_GATEWAYS]),
        (PAYMENT_PROCESS, DISPLAY_LABELS[PAYMENT_PROCESS]),
        (PAYMENT_REFUND, DISPLAY_LABELS[PAYMENT_REFUND]),
        (PAYMENT_VOID, DISPLAY_LABELS[PAYMENT_VOID]),
    ]

    PAYMENT_EVENTS = [
        PAYMENT_AUTHORIZE,
        PAYMENT_CAPTURE,
        PAYMENT_CONFIRM,
        PAYMENT_LIST_GATEWAYS,
        PAYMENT_PROCESS,
        PAYMENT_REFUND,
        PAYMENT_VOID,
    ]

    PERMISSIONS = {
        ORDER_CREATED: OrderPermissions.MANAGE_ORDERS,
        ORDER_CONFIRMED: OrderPermissions.MANAGE_ORDERS,
        ORDER_FULLY_PAID: OrderPermissions.MANAGE_ORDERS,
        ORDER_UPDATED: OrderPermissions.MANAGE_ORDERS,
        ORDER_CANCELLED: OrderPermissions.MANAGE_ORDERS,
        ORDER_FULFILLED: OrderPermissions.MANAGE_ORDERS,
        INVOICE_REQUESTED: OrderPermissions.MANAGE_ORDERS,
        INVOICE_DELETED: OrderPermissions.MANAGE_ORDERS,
        INVOICE_SENT: OrderPermissions.MANAGE_ORDERS,
        CUSTOMER_CREATED: AccountPermissions.MANAGE_USERS,
        CUSTOMER_UPDATED: AccountPermissions.MANAGE_USERS,
        PRODUCT_CREATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_DELETED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_CREATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_DELETED: ProductPermissions.MANAGE_PRODUCTS,
        CHECKOUT_CREATED: CheckoutPermissions.MANAGE_CHECKOUTS,
        CHECKOUT_UPDATED: CheckoutPermissions.MANAGE_CHECKOUTS,
        FULFILLMENT_CREATED: OrderPermissions.MANAGE_ORDERS,
        NOTIFY_USER: AccountPermissions.MANAGE_USERS,
        PAGE_CREATED: PagePermissions.MANAGE_PAGES,
        PAGE_UPDATED: PagePermissions.MANAGE_PAGES,
        PAGE_DELETED: PagePermissions.MANAGE_PAGES,
        PAYMENT_AUTHORIZE: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_CAPTURE: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_CONFIRM: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_LIST_GATEWAYS: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_PROCESS: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_REFUND: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_VOID: PaymentPermissions.HANDLE_PAYMENTS,
    }
