class WebhookEventType:
    ANY = "any_events"
    ORDER_CREATED = "order_created"
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_FULLY_PAID = "order_fully_paid"
    ORDER_UPDATED = "order_updated"
    ORDER_CANCELLED = "order_cancelled"
    FULFILLMENT_CANCELED = "fulfillment_canceled"
    ORDER_FULFILLED = "order_fulfilled"

    DRAFT_ORDER_CREATED = "draft_order_created"
    DRAFT_ORDER_UPDATED = "draft_order_updated"
    DRAFT_ORDER_DELETED = "draft_order_deleted"

    SALE_CREATED = "sale_created"
    SALE_UPDATED = "sale_updated"
    SALE_DELETED = "sale_deleted"

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

    PRODUCT_VARIANT_OUT_OF_STOCK = "product_variant_out_of_stock"
    PRODUCT_VARIANT_BACK_IN_STOCK = "product_variant_back_in_stock"

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

    SHIPPING_LIST_METHODS_FOR_CHECKOUT = "shipping_list_methods_for_checkout"
    CHECKOUT_FILTER_SHIPPING_METHODS = "checkout_filter_shipping_methods"
    ORDER_FILTER_SHIPPING_METHODS = "order_filter_shipping_methods"

    TRANSLATION_CREATED = "translation_created"
    TRANSLATION_UPDATED = "translation_updated"

    DISPLAY_LABELS = {
        ANY: "Any events",
        ORDER_CREATED: "Order created",
        ORDER_CONFIRMED: "Order confirmed",
        ORDER_FULLY_PAID: "Order paid",
        ORDER_UPDATED: "Order updated",
        ORDER_CANCELLED: "Order cancelled",
        ORDER_FULFILLED: "Order fulfilled",
        DRAFT_ORDER_CREATED: "Draft order created",
        DRAFT_ORDER_UPDATED: "Draft order updated",
        DRAFT_ORDER_DELETED: "Draft order deleted",
        SALE_CREATED: "Sale created",
        SALE_UPDATED: "Sale updated",
        SALE_DELETED: "Sale deleted",
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
        PRODUCT_VARIANT_OUT_OF_STOCK: "Product variant stock changed",
        PRODUCT_VARIANT_BACK_IN_STOCK: "Product variant back in stock",
        CHECKOUT_CREATED: "Checkout created",
        CHECKOUT_UPDATED: "Checkout updated",
        FULFILLMENT_CREATED: "Fulfillment created",
        FULFILLMENT_CANCELED: "Fulfillment cancelled",
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
        SHIPPING_LIST_METHODS_FOR_CHECKOUT: "Shipping list methods for checkout",
        ORDER_FILTER_SHIPPING_METHODS: "Filter order shipping methods",
        CHECKOUT_FILTER_SHIPPING_METHODS: "Filter checkout shipping methods",
        TRANSLATION_CREATED: "Create translation",
        TRANSLATION_UPDATED: "Update translation",
    }

    CHOICES = [
        (ANY, DISPLAY_LABELS[ANY]),
        (ORDER_CREATED, DISPLAY_LABELS[ORDER_CREATED]),
        (ORDER_CONFIRMED, DISPLAY_LABELS[ORDER_CONFIRMED]),
        (ORDER_FULLY_PAID, DISPLAY_LABELS[ORDER_FULLY_PAID]),
        (ORDER_UPDATED, DISPLAY_LABELS[ORDER_UPDATED]),
        (ORDER_CANCELLED, DISPLAY_LABELS[ORDER_CANCELLED]),
        (ORDER_FULFILLED, DISPLAY_LABELS[ORDER_FULFILLED]),
        (DRAFT_ORDER_CREATED, DISPLAY_LABELS[DRAFT_ORDER_CREATED]),
        (DRAFT_ORDER_UPDATED, DISPLAY_LABELS[DRAFT_ORDER_UPDATED]),
        (DRAFT_ORDER_DELETED, DISPLAY_LABELS[DRAFT_ORDER_DELETED]),
        (SALE_CREATED, DISPLAY_LABELS[SALE_CREATED]),
        (SALE_UPDATED, DISPLAY_LABELS[SALE_UPDATED]),
        (SALE_DELETED, DISPLAY_LABELS[SALE_DELETED]),
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
        (PRODUCT_VARIANT_OUT_OF_STOCK, DISPLAY_LABELS[PRODUCT_VARIANT_OUT_OF_STOCK]),
        (PRODUCT_VARIANT_BACK_IN_STOCK, DISPLAY_LABELS[PRODUCT_VARIANT_BACK_IN_STOCK]),
        (CHECKOUT_CREATED, DISPLAY_LABELS[CHECKOUT_CREATED]),
        (CHECKOUT_UPDATED, DISPLAY_LABELS[CHECKOUT_UPDATED]),
        (FULFILLMENT_CREATED, DISPLAY_LABELS[FULFILLMENT_CREATED]),
        (FULFILLMENT_CANCELED, DISPLAY_LABELS[FULFILLMENT_CANCELED]),
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
        (
            SHIPPING_LIST_METHODS_FOR_CHECKOUT,
            DISPLAY_LABELS[SHIPPING_LIST_METHODS_FOR_CHECKOUT],
        ),
        (ORDER_FILTER_SHIPPING_METHODS, DISPLAY_LABELS[ORDER_FILTER_SHIPPING_METHODS]),
        (
            CHECKOUT_FILTER_SHIPPING_METHODS,
            DISPLAY_LABELS[CHECKOUT_FILTER_SHIPPING_METHODS],
        ),
        (TRANSLATION_CREATED, DISPLAY_LABELS[TRANSLATION_CREATED]),
        (TRANSLATION_UPDATED, DISPLAY_LABELS[TRANSLATION_UPDATED]),
    ]
