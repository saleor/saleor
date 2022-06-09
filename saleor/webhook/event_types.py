from ..core.permissions import (
    AccountPermissions,
    AppPermission,
    ChannelPermissions,
    CheckoutPermissions,
    DiscountPermissions,
    GiftcardPermissions,
    MenuPermissions,
    OrderPermissions,
    PagePermissions,
    PageTypePermissions,
    PaymentPermissions,
    ProductPermissions,
    ShippingPermissions,
    SitePermissions,
)


class WebhookEventAsyncType:
    ANY = "any_events"

    ADDRESS_CREATED = "address_created"
    ADDRESS_UPDATED = "address_updated"
    ADDRESS_DELETED = "address_deleted"

    APP_INSTALLED = "app_installed"
    APP_UPDATED = "app_updated"
    APP_DELETED = "app_deleted"
    APP_STATUS_CHANGED = "app_status_changed"

    CATEGORY_CREATED = "category_created"
    CATEGORY_UPDATED = "category_updated"
    CATEGORY_DELETED = "category_deleted"

    CHANNEL_CREATED = "channel_created"
    CHANNEL_UPDATED = "channel_updated"
    CHANNEL_DELETED = "channel_deleted"
    CHANNEL_STATUS_CHANGED = "channel_status_changed"

    GIFT_CARD_CREATED = "gift_card_created"
    GIFT_CARD_UPDATED = "gift_card_updated"
    GIFT_CARD_DELETED = "gift_card_deleted"
    GIFT_CARD_STATUS_CHANGED = "gift_card_status_changed"

    MENU_CREATED = "menu_created"
    MENU_UPDATED = "menu_updated"
    MENU_DELETED = "menu_deleted"
    MENU_ITEM_CREATED = "menu_item_created"
    MENU_ITEM_UPDATED = "menu_item_updated"
    MENU_ITEM_DELETED = "menu_item_deleted"

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

    COLLECTION_CREATED = "collection_created"
    COLLECTION_UPDATED = "collection_updated"
    COLLECTION_DELETED = "collection_deleted"

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

    PAGE_TYPE_CREATED = "page_type_created"
    PAGE_TYPE_UPDATED = "page_type_updated"
    PAGE_TYPE_DELETED = "page_type_deleted"

    SHIPPING_PRICE_CREATED = "shipping_price_created"
    SHIPPING_PRICE_UPDATED = "shipping_price_updated"
    SHIPPING_PRICE_DELETED = "shipping_price_deleted"

    SHIPPING_ZONE_CREATED = "shipping_zone_created"
    SHIPPING_ZONE_UPDATED = "shipping_zone_updated"
    SHIPPING_ZONE_DELETED = "shipping_zone_deleted"

    TRANSACTION_ACTION_REQUEST = "transaction_action_request"

    TRANSLATION_CREATED = "translation_created"
    TRANSLATION_UPDATED = "translation_updated"

    WAREHOUSE_CREATED = "warehouse_created"
    WAREHOUSE_UPDATED = "warehouse_updated"
    WAREHOUSE_DELETED = "warehouse_deleted"

    VOUCHER_CREATED = "voucher_created"
    VOUCHER_UPDATED = "voucher_updated"
    VOUCHER_DELETED = "voucher_deleted"

    OBSERVABILITY = "observability"

    DISPLAY_LABELS = {
        ANY: "Any events",
        ADDRESS_CREATED: "Address created",
        ADDRESS_UPDATED: "Address updated",
        ADDRESS_DELETED: "Address deleted",
        APP_INSTALLED: "App created",
        APP_UPDATED: "App updated",
        APP_DELETED: "App deleted",
        APP_STATUS_CHANGED: "App status changed",
        CATEGORY_CREATED: "Category created",
        CATEGORY_UPDATED: "Category updated",
        CATEGORY_DELETED: "Category deleted",
        CHANNEL_CREATED: "Channel created",
        CHANNEL_UPDATED: "Channel updated",
        CHANNEL_DELETED: "Channel deleted",
        CHANNEL_STATUS_CHANGED: "Channel status changed",
        GIFT_CARD_CREATED: "Gift card created",
        GIFT_CARD_UPDATED: "Gift card updated",
        GIFT_CARD_DELETED: "Gift card deleted",
        GIFT_CARD_STATUS_CHANGED: "Gift card status changed",
        MENU_CREATED: "Menu created",
        MENU_UPDATED: "Menu updated",
        MENU_DELETED: "Menu deleted",
        MENU_ITEM_CREATED: "Menu item created",
        MENU_ITEM_UPDATED: "Menu item updated",
        MENU_ITEM_DELETED: "Menu item deleted",
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
        COLLECTION_CREATED: "Collection created",
        COLLECTION_UPDATED: "Collection updated",
        COLLECTION_DELETED: "Collection deleted",
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
        FULFILLMENT_CREATED: "Fulfillment_created",
        FULFILLMENT_CANCELED: "Fulfillment_cancelled",
        NOTIFY_USER: "Notify user",
        PAGE_CREATED: "Page Created",
        PAGE_UPDATED: "Page Updated",
        PAGE_DELETED: "Page Deleted",
        PAGE_TYPE_CREATED: "Page type created",
        PAGE_TYPE_UPDATED: "Page type updated",
        PAGE_TYPE_DELETED: "Page type deleted",
        SHIPPING_PRICE_CREATED: "Shipping price created",
        SHIPPING_PRICE_UPDATED: "Shipping price updated",
        SHIPPING_PRICE_DELETED: "Shipping price deleted",
        SHIPPING_ZONE_CREATED: "Shipping zone created",
        SHIPPING_ZONE_UPDATED: "Shipping zone updated",
        SHIPPING_ZONE_DELETED: "Shipping zone deleted",
        TRANSACTION_ACTION_REQUEST: "Payment action request",
        TRANSLATION_CREATED: "Create translation",
        TRANSLATION_UPDATED: "Update translation",
        WAREHOUSE_CREATED: "Warehouse created",
        WAREHOUSE_UPDATED: "Warehouse updated",
        WAREHOUSE_DELETED: "Warehouse deleted",
        VOUCHER_CREATED: "Voucher created",
        VOUCHER_UPDATED: "Voucher updated",
        VOUCHER_DELETED: "Voucher deleted",
        OBSERVABILITY: "Observability",
    }

    CHOICES = [
        (ANY, DISPLAY_LABELS[ANY]),
        (ADDRESS_CREATED, DISPLAY_LABELS[ADDRESS_CREATED]),
        (ADDRESS_UPDATED, DISPLAY_LABELS[ADDRESS_UPDATED]),
        (ADDRESS_DELETED, DISPLAY_LABELS[ADDRESS_DELETED]),
        (APP_INSTALLED, DISPLAY_LABELS[APP_INSTALLED]),
        (APP_UPDATED, DISPLAY_LABELS[APP_UPDATED]),
        (APP_DELETED, DISPLAY_LABELS[APP_DELETED]),
        (APP_STATUS_CHANGED, DISPLAY_LABELS[APP_STATUS_CHANGED]),
        (CATEGORY_CREATED, DISPLAY_LABELS[CATEGORY_CREATED]),
        (CATEGORY_UPDATED, DISPLAY_LABELS[CATEGORY_UPDATED]),
        (CATEGORY_DELETED, DISPLAY_LABELS[CATEGORY_DELETED]),
        (CHANNEL_CREATED, DISPLAY_LABELS[CHANNEL_CREATED]),
        (CHANNEL_UPDATED, DISPLAY_LABELS[CHANNEL_UPDATED]),
        (CHANNEL_DELETED, DISPLAY_LABELS[CHANNEL_DELETED]),
        (CHANNEL_STATUS_CHANGED, DISPLAY_LABELS[CHANNEL_STATUS_CHANGED]),
        (GIFT_CARD_CREATED, DISPLAY_LABELS[GIFT_CARD_CREATED]),
        (GIFT_CARD_UPDATED, DISPLAY_LABELS[GIFT_CARD_UPDATED]),
        (GIFT_CARD_DELETED, DISPLAY_LABELS[GIFT_CARD_DELETED]),
        (GIFT_CARD_STATUS_CHANGED, DISPLAY_LABELS[GIFT_CARD_STATUS_CHANGED]),
        (MENU_CREATED, DISPLAY_LABELS[MENU_CREATED]),
        (MENU_UPDATED, DISPLAY_LABELS[MENU_UPDATED]),
        (MENU_DELETED, DISPLAY_LABELS[MENU_DELETED]),
        (MENU_ITEM_CREATED, DISPLAY_LABELS[MENU_ITEM_CREATED]),
        (MENU_ITEM_UPDATED, DISPLAY_LABELS[MENU_ITEM_UPDATED]),
        (MENU_ITEM_DELETED, DISPLAY_LABELS[MENU_ITEM_DELETED]),
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
        (COLLECTION_CREATED, DISPLAY_LABELS[COLLECTION_CREATED]),
        (COLLECTION_UPDATED, DISPLAY_LABELS[COLLECTION_UPDATED]),
        (COLLECTION_DELETED, DISPLAY_LABELS[COLLECTION_DELETED]),
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
        (PAGE_TYPE_CREATED, DISPLAY_LABELS[PAGE_TYPE_CREATED]),
        (PAGE_TYPE_UPDATED, DISPLAY_LABELS[PAGE_TYPE_UPDATED]),
        (PAGE_TYPE_DELETED, DISPLAY_LABELS[PAGE_TYPE_DELETED]),
        (SHIPPING_PRICE_CREATED, DISPLAY_LABELS[SHIPPING_PRICE_CREATED]),
        (SHIPPING_PRICE_UPDATED, DISPLAY_LABELS[SHIPPING_PRICE_UPDATED]),
        (SHIPPING_PRICE_DELETED, DISPLAY_LABELS[SHIPPING_PRICE_DELETED]),
        (SHIPPING_ZONE_CREATED, DISPLAY_LABELS[SHIPPING_ZONE_CREATED]),
        (SHIPPING_ZONE_UPDATED, DISPLAY_LABELS[SHIPPING_ZONE_UPDATED]),
        (SHIPPING_ZONE_DELETED, DISPLAY_LABELS[SHIPPING_ZONE_DELETED]),
        (TRANSACTION_ACTION_REQUEST, DISPLAY_LABELS[TRANSACTION_ACTION_REQUEST]),
        (TRANSLATION_CREATED, DISPLAY_LABELS[TRANSLATION_CREATED]),
        (TRANSLATION_UPDATED, DISPLAY_LABELS[TRANSLATION_UPDATED]),
        (WAREHOUSE_CREATED, DISPLAY_LABELS[WAREHOUSE_CREATED]),
        (WAREHOUSE_UPDATED, DISPLAY_LABELS[WAREHOUSE_UPDATED]),
        (WAREHOUSE_DELETED, DISPLAY_LABELS[WAREHOUSE_DELETED]),
        (VOUCHER_CREATED, DISPLAY_LABELS[VOUCHER_CREATED]),
        (VOUCHER_UPDATED, DISPLAY_LABELS[VOUCHER_UPDATED]),
        (VOUCHER_DELETED, DISPLAY_LABELS[VOUCHER_DELETED]),
        (OBSERVABILITY, DISPLAY_LABELS[OBSERVABILITY]),
    ]

    ALL = [event[0] for event in CHOICES]

    PERMISSIONS = {
        ADDRESS_CREATED: AccountPermissions.MANAGE_USERS,
        ADDRESS_UPDATED: AccountPermissions.MANAGE_USERS,
        ADDRESS_DELETED: AccountPermissions.MANAGE_USERS,
        APP_INSTALLED: AppPermission.MANAGE_APPS,
        APP_UPDATED: AppPermission.MANAGE_APPS,
        APP_DELETED: AppPermission.MANAGE_APPS,
        APP_STATUS_CHANGED: AppPermission.MANAGE_APPS,
        CATEGORY_CREATED: ProductPermissions.MANAGE_PRODUCTS,
        CATEGORY_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        CATEGORY_DELETED: ProductPermissions.MANAGE_PRODUCTS,
        CHANNEL_CREATED: ChannelPermissions.MANAGE_CHANNELS,
        CHANNEL_UPDATED: ChannelPermissions.MANAGE_CHANNELS,
        CHANNEL_DELETED: ChannelPermissions.MANAGE_CHANNELS,
        CHANNEL_STATUS_CHANGED: ChannelPermissions.MANAGE_CHANNELS,
        GIFT_CARD_CREATED: GiftcardPermissions.MANAGE_GIFT_CARD,
        GIFT_CARD_UPDATED: GiftcardPermissions.MANAGE_GIFT_CARD,
        GIFT_CARD_DELETED: GiftcardPermissions.MANAGE_GIFT_CARD,
        GIFT_CARD_STATUS_CHANGED: GiftcardPermissions.MANAGE_GIFT_CARD,
        MENU_CREATED: MenuPermissions.MANAGE_MENUS,
        MENU_UPDATED: MenuPermissions.MANAGE_MENUS,
        MENU_DELETED: MenuPermissions.MANAGE_MENUS,
        MENU_ITEM_CREATED: MenuPermissions.MANAGE_MENUS,
        MENU_ITEM_UPDATED: MenuPermissions.MANAGE_MENUS,
        MENU_ITEM_DELETED: MenuPermissions.MANAGE_MENUS,
        ORDER_CREATED: OrderPermissions.MANAGE_ORDERS,
        ORDER_CONFIRMED: OrderPermissions.MANAGE_ORDERS,
        ORDER_FULLY_PAID: OrderPermissions.MANAGE_ORDERS,
        ORDER_UPDATED: OrderPermissions.MANAGE_ORDERS,
        ORDER_CANCELLED: OrderPermissions.MANAGE_ORDERS,
        ORDER_FULFILLED: OrderPermissions.MANAGE_ORDERS,
        DRAFT_ORDER_CREATED: OrderPermissions.MANAGE_ORDERS,
        DRAFT_ORDER_DELETED: OrderPermissions.MANAGE_ORDERS,
        DRAFT_ORDER_UPDATED: OrderPermissions.MANAGE_ORDERS,
        SALE_CREATED: DiscountPermissions.MANAGE_DISCOUNTS,
        SALE_UPDATED: DiscountPermissions.MANAGE_DISCOUNTS,
        SALE_DELETED: DiscountPermissions.MANAGE_DISCOUNTS,
        INVOICE_REQUESTED: OrderPermissions.MANAGE_ORDERS,
        INVOICE_DELETED: OrderPermissions.MANAGE_ORDERS,
        INVOICE_SENT: OrderPermissions.MANAGE_ORDERS,
        CUSTOMER_CREATED: AccountPermissions.MANAGE_USERS,
        CUSTOMER_UPDATED: AccountPermissions.MANAGE_USERS,
        COLLECTION_CREATED: ProductPermissions.MANAGE_PRODUCTS,
        COLLECTION_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        COLLECTION_DELETED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_CREATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_DELETED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_CREATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_DELETED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_BACK_IN_STOCK: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_OUT_OF_STOCK: ProductPermissions.MANAGE_PRODUCTS,
        CHECKOUT_CREATED: CheckoutPermissions.MANAGE_CHECKOUTS,
        CHECKOUT_UPDATED: CheckoutPermissions.MANAGE_CHECKOUTS,
        FULFILLMENT_CREATED: OrderPermissions.MANAGE_ORDERS,
        FULFILLMENT_CANCELED: OrderPermissions.MANAGE_ORDERS,
        NOTIFY_USER: AccountPermissions.MANAGE_USERS,
        PAGE_CREATED: PagePermissions.MANAGE_PAGES,
        PAGE_UPDATED: PagePermissions.MANAGE_PAGES,
        PAGE_DELETED: PagePermissions.MANAGE_PAGES,
        PAGE_TYPE_CREATED: PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
        PAGE_TYPE_UPDATED: PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
        PAGE_TYPE_DELETED: PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
        SHIPPING_PRICE_CREATED: ShippingPermissions.MANAGE_SHIPPING,
        SHIPPING_PRICE_UPDATED: ShippingPermissions.MANAGE_SHIPPING,
        SHIPPING_PRICE_DELETED: ShippingPermissions.MANAGE_SHIPPING,
        SHIPPING_ZONE_CREATED: ShippingPermissions.MANAGE_SHIPPING,
        SHIPPING_ZONE_UPDATED: ShippingPermissions.MANAGE_SHIPPING,
        SHIPPING_ZONE_DELETED: ShippingPermissions.MANAGE_SHIPPING,
        TRANSACTION_ACTION_REQUEST: PaymentPermissions.HANDLE_PAYMENTS,
        TRANSLATION_CREATED: SitePermissions.MANAGE_TRANSLATIONS,
        TRANSLATION_UPDATED: SitePermissions.MANAGE_TRANSLATIONS,
        VOUCHER_CREATED: DiscountPermissions.MANAGE_DISCOUNTS,
        VOUCHER_UPDATED: DiscountPermissions.MANAGE_DISCOUNTS,
        VOUCHER_DELETED: DiscountPermissions.MANAGE_DISCOUNTS,
        WAREHOUSE_CREATED: ProductPermissions.MANAGE_PRODUCTS,
        WAREHOUSE_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        WAREHOUSE_DELETED: ProductPermissions.MANAGE_PRODUCTS,
        OBSERVABILITY: AppPermission.MANAGE_OBSERVABILITY,
    }


class WebhookEventSyncType:
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

    DISPLAY_LABELS = {
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
    }

    CHOICES = [
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
    ]

    ALL = [event[0] for event in CHOICES]

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
        PAYMENT_AUTHORIZE: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_CAPTURE: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_CONFIRM: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_LIST_GATEWAYS: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_PROCESS: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_REFUND: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_VOID: PaymentPermissions.HANDLE_PAYMENTS,
        SHIPPING_LIST_METHODS_FOR_CHECKOUT: ShippingPermissions.MANAGE_SHIPPING,
        ORDER_FILTER_SHIPPING_METHODS: OrderPermissions.MANAGE_ORDERS,
        CHECKOUT_FILTER_SHIPPING_METHODS: CheckoutPermissions.MANAGE_CHECKOUTS,
    }


SUBSCRIBABLE_EVENTS = [
    WebhookEventAsyncType.ADDRESS_CREATED,
    WebhookEventAsyncType.ADDRESS_UPDATED,
    WebhookEventAsyncType.ADDRESS_DELETED,
    WebhookEventAsyncType.APP_INSTALLED,
    WebhookEventAsyncType.APP_UPDATED,
    WebhookEventAsyncType.APP_DELETED,
    WebhookEventAsyncType.APP_STATUS_CHANGED,
    WebhookEventAsyncType.CATEGORY_CREATED,
    WebhookEventAsyncType.CATEGORY_UPDATED,
    WebhookEventAsyncType.CATEGORY_DELETED,
    WebhookEventAsyncType.CHANNEL_CREATED,
    WebhookEventAsyncType.CHANNEL_UPDATED,
    WebhookEventAsyncType.CHANNEL_DELETED,
    WebhookEventAsyncType.CHANNEL_STATUS_CHANGED,
    WebhookEventAsyncType.GIFT_CARD_CREATED,
    WebhookEventAsyncType.GIFT_CARD_UPDATED,
    WebhookEventAsyncType.GIFT_CARD_DELETED,
    WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED,
    WebhookEventAsyncType.MENU_CREATED,
    WebhookEventAsyncType.MENU_UPDATED,
    WebhookEventAsyncType.MENU_DELETED,
    WebhookEventAsyncType.MENU_ITEM_CREATED,
    WebhookEventAsyncType.MENU_ITEM_UPDATED,
    WebhookEventAsyncType.MENU_ITEM_DELETED,
    WebhookEventAsyncType.ORDER_CREATED,
    WebhookEventAsyncType.ORDER_UPDATED,
    WebhookEventAsyncType.ORDER_CONFIRMED,
    WebhookEventAsyncType.ORDER_FULLY_PAID,
    WebhookEventAsyncType.ORDER_FULFILLED,
    WebhookEventAsyncType.ORDER_CANCELLED,
    WebhookEventAsyncType.DRAFT_ORDER_CREATED,
    WebhookEventAsyncType.DRAFT_ORDER_UPDATED,
    WebhookEventAsyncType.DRAFT_ORDER_DELETED,
    WebhookEventAsyncType.PRODUCT_CREATED,
    WebhookEventAsyncType.PRODUCT_UPDATED,
    WebhookEventAsyncType.PRODUCT_DELETED,
    WebhookEventAsyncType.PRODUCT_VARIANT_DELETED,
    WebhookEventAsyncType.PRODUCT_VARIANT_CREATED,
    WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
    WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK,
    WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK,
    WebhookEventAsyncType.SALE_CREATED,
    WebhookEventAsyncType.SALE_UPDATED,
    WebhookEventAsyncType.SALE_DELETED,
    WebhookEventAsyncType.INVOICE_REQUESTED,
    WebhookEventAsyncType.INVOICE_DELETED,
    WebhookEventAsyncType.INVOICE_SENT,
    WebhookEventAsyncType.FULFILLMENT_CREATED,
    WebhookEventAsyncType.FULFILLMENT_CANCELED,
    WebhookEventAsyncType.CUSTOMER_CREATED,
    WebhookEventAsyncType.CUSTOMER_UPDATED,
    WebhookEventAsyncType.COLLECTION_CREATED,
    WebhookEventAsyncType.COLLECTION_UPDATED,
    WebhookEventAsyncType.COLLECTION_DELETED,
    WebhookEventAsyncType.CHECKOUT_CREATED,
    WebhookEventAsyncType.CHECKOUT_UPDATED,
    WebhookEventAsyncType.PAGE_CREATED,
    WebhookEventAsyncType.PAGE_UPDATED,
    WebhookEventAsyncType.PAGE_DELETED,
    WebhookEventAsyncType.PAGE_TYPE_CREATED,
    WebhookEventAsyncType.PAGE_TYPE_UPDATED,
    WebhookEventAsyncType.PAGE_TYPE_DELETED,
    WebhookEventAsyncType.SHIPPING_PRICE_CREATED,
    WebhookEventAsyncType.SHIPPING_PRICE_UPDATED,
    WebhookEventAsyncType.SHIPPING_PRICE_DELETED,
    WebhookEventAsyncType.SHIPPING_ZONE_CREATED,
    WebhookEventAsyncType.SHIPPING_ZONE_UPDATED,
    WebhookEventAsyncType.SHIPPING_ZONE_DELETED,
    WebhookEventAsyncType.TRANSACTION_ACTION_REQUEST,
    WebhookEventAsyncType.TRANSLATION_CREATED,
    WebhookEventAsyncType.TRANSLATION_UPDATED,
    WebhookEventAsyncType.VOUCHER_CREATED,
    WebhookEventAsyncType.VOUCHER_UPDATED,
    WebhookEventAsyncType.VOUCHER_DELETED,
    WebhookEventAsyncType.WAREHOUSE_CREATED,
    WebhookEventAsyncType.WAREHOUSE_UPDATED,
    WebhookEventAsyncType.WAREHOUSE_DELETED,
]
