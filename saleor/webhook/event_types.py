from ..permission.enums import (
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

    ACCOUNT_CONFIRMATION_REQUESTED = "account_confirmation_requested"
    ACCOUNT_CHANGE_EMAIL_REQUESTED = "account_change_email_requested"
    ACCOUNT_DELETE_REQUESTED = "account_delete_requested"

    ADDRESS_CREATED = "address_created"
    ADDRESS_UPDATED = "address_updated"
    ADDRESS_DELETED = "address_deleted"

    APP_INSTALLED = "app_installed"
    APP_UPDATED = "app_updated"
    APP_DELETED = "app_deleted"
    APP_STATUS_CHANGED = "app_status_changed"

    ATTRIBUTE_CREATED = "attribute_created"
    ATTRIBUTE_UPDATED = "attribute_updated"
    ATTRIBUTE_DELETED = "attribute_deleted"

    ATTRIBUTE_VALUE_CREATED = "attribute_value_created"
    ATTRIBUTE_VALUE_UPDATED = "attribute_value_updated"
    ATTRIBUTE_VALUE_DELETED = "attribute_value_deleted"

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
    GIFT_CARD_SENT = "gift_card_sent"
    GIFT_CARD_STATUS_CHANGED = "gift_card_status_changed"
    GIFT_CARD_METADATA_UPDATED = "gift_card_metadata_updated"

    MENU_CREATED = "menu_created"
    MENU_UPDATED = "menu_updated"
    MENU_DELETED = "menu_deleted"
    MENU_ITEM_CREATED = "menu_item_created"
    MENU_ITEM_UPDATED = "menu_item_updated"
    MENU_ITEM_DELETED = "menu_item_deleted"

    ORDER_CREATED = "order_created"
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_PAID = "order_paid"
    ORDER_FULLY_PAID = "order_fully_paid"
    ORDER_REFUNDED = "order_refunded"
    ORDER_FULLY_REFUNDED = "order_fully_refunded"
    ORDER_UPDATED = "order_updated"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_EXPIRED = "order_expired"
    ORDER_FULFILLED = "order_fulfilled"
    ORDER_METADATA_UPDATED = "order_metadata_updated"
    ORDER_BULK_CREATED = "order_bulk_created"

    FULFILLMENT_CREATED = "fulfillment_created"
    FULFILLMENT_CANCELED = "fulfillment_canceled"
    FULFILLMENT_APPROVED = "fulfillment_approved"
    FULFILLMENT_METADATA_UPDATED = "fulfillment_metadata_updated"

    DRAFT_ORDER_CREATED = "draft_order_created"
    DRAFT_ORDER_UPDATED = "draft_order_updated"
    DRAFT_ORDER_DELETED = "draft_order_deleted"

    SALE_CREATED = "sale_created"
    SALE_UPDATED = "sale_updated"
    SALE_DELETED = "sale_deleted"
    SALE_TOGGLE = "sale_toggle"

    INVOICE_REQUESTED = "invoice_requested"
    INVOICE_DELETED = "invoice_deleted"
    INVOICE_SENT = "invoice_sent"

    CUSTOMER_CREATED = "customer_created"
    CUSTOMER_UPDATED = "customer_updated"
    CUSTOMER_DELETED = "customer_deleted"
    CUSTOMER_METADATA_UPDATED = "customer_metadata_updated"

    COLLECTION_CREATED = "collection_created"
    COLLECTION_UPDATED = "collection_updated"
    COLLECTION_DELETED = "collection_deleted"
    COLLECTION_METADATA_UPDATED = "collection_metadata_updated"

    PRODUCT_CREATED = "product_created"
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_DELETED = "product_deleted"
    PRODUCT_METADATA_UPDATED = "product_metadata_updated"

    PRODUCT_MEDIA_CREATED = "product_media_created"
    PRODUCT_MEDIA_UPDATED = "product_media_updated"
    PRODUCT_MEDIA_DELETED = "product_media_deleted"

    PRODUCT_VARIANT_CREATED = "product_variant_created"
    PRODUCT_VARIANT_UPDATED = "product_variant_updated"
    PRODUCT_VARIANT_DELETED = "product_variant_deleted"
    PRODUCT_VARIANT_METADATA_UPDATED = "product_variant_metadata_updated"

    PRODUCT_VARIANT_OUT_OF_STOCK = "product_variant_out_of_stock"
    PRODUCT_VARIANT_BACK_IN_STOCK = "product_variant_back_in_stock"
    PRODUCT_VARIANT_STOCK_UPDATED = "product_variant_stock_updated"

    CHECKOUT_CREATED = "checkout_created"
    CHECKOUT_UPDATED = "checkout_updated"
    CHECKOUT_FULLY_PAID = "checkout_fully_paid"
    CHECKOUT_METADATA_UPDATED = "checkout_metadata_updated"

    NOTIFY_USER = "notify_user"

    PAGE_CREATED = "page_created"
    PAGE_UPDATED = "page_updated"
    PAGE_DELETED = "page_deleted"

    PAGE_TYPE_CREATED = "page_type_created"
    PAGE_TYPE_UPDATED = "page_type_updated"
    PAGE_TYPE_DELETED = "page_type_deleted"

    PERMISSION_GROUP_CREATED = "permission_group_created"
    PERMISSION_GROUP_UPDATED = "permission_group_updated"
    PERMISSION_GROUP_DELETED = "permission_group_deleted"

    SHIPPING_PRICE_CREATED = "shipping_price_created"
    SHIPPING_PRICE_UPDATED = "shipping_price_updated"
    SHIPPING_PRICE_DELETED = "shipping_price_deleted"

    SHIPPING_ZONE_CREATED = "shipping_zone_created"
    SHIPPING_ZONE_UPDATED = "shipping_zone_updated"
    SHIPPING_ZONE_DELETED = "shipping_zone_deleted"
    SHIPPING_ZONE_METADATA_UPDATED = "shipping_zone_metadata_updated"

    STAFF_CREATED = "staff_created"
    STAFF_UPDATED = "staff_updated"
    STAFF_DELETED = "staff_deleted"

    TRANSACTION_ITEM_METADATA_UPDATED = "transaction_item_metadata_updated"

    TRANSLATION_CREATED = "translation_created"
    TRANSLATION_UPDATED = "translation_updated"

    WAREHOUSE_CREATED = "warehouse_created"
    WAREHOUSE_UPDATED = "warehouse_updated"
    WAREHOUSE_DELETED = "warehouse_deleted"
    WAREHOUSE_METADATA_UPDATED = "warehouse_metadata_updated"

    VOUCHER_CREATED = "voucher_created"
    VOUCHER_UPDATED = "voucher_updated"
    VOUCHER_DELETED = "voucher_deleted"
    VOUCHER_METADATA_UPDATED = "voucher_metadata_updated"

    OBSERVABILITY = "observability"

    THUMBNAIL_CREATED = "thumbnail_created"

    DISPLAY_LABELS = {
        ANY: "Any events",
        ACCOUNT_CONFIRMATION_REQUESTED: "Account confirmation requested",
        ACCOUNT_CHANGE_EMAIL_REQUESTED: "Account change email requested",
        ACCOUNT_DELETE_REQUESTED: "Account delete requested",
        ADDRESS_CREATED: "Address created",
        ADDRESS_UPDATED: "Address updated",
        ADDRESS_DELETED: "Address deleted",
        APP_INSTALLED: "App created",
        APP_UPDATED: "App updated",
        APP_DELETED: "App deleted",
        APP_STATUS_CHANGED: "App status changed",
        ATTRIBUTE_CREATED: "Attribute created",
        ATTRIBUTE_UPDATED: "Attribute updated",
        ATTRIBUTE_DELETED: "Attribute deleted",
        ATTRIBUTE_VALUE_CREATED: "Attribute value created",
        ATTRIBUTE_VALUE_UPDATED: "Attribute value updated",
        ATTRIBUTE_VALUE_DELETED: "Attribute value deleted",
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
        GIFT_CARD_SENT: "Gift card sent",
        GIFT_CARD_STATUS_CHANGED: "Gift card status changed",
        GIFT_CARD_METADATA_UPDATED: "Gift card metadata updated",
        MENU_CREATED: "Menu created",
        MENU_UPDATED: "Menu updated",
        MENU_DELETED: "Menu deleted",
        MENU_ITEM_CREATED: "Menu item created",
        MENU_ITEM_UPDATED: "Menu item updated",
        MENU_ITEM_DELETED: "Menu item deleted",
        ORDER_CREATED: "Order created",
        ORDER_CONFIRMED: "Order confirmed",
        ORDER_PAID: "Order paid",
        ORDER_FULLY_PAID: "Order fully paid",
        ORDER_REFUNDED: "Order refunded",
        ORDER_FULLY_REFUNDED: "Order fully refunded",
        ORDER_UPDATED: "Order updated",
        ORDER_CANCELLED: "Order cancelled",
        ORDER_EXPIRED: "Order expired",
        ORDER_FULFILLED: "Order fulfilled",
        ORDER_METADATA_UPDATED: "Order metadata updated",
        ORDER_BULK_CREATED: "Order bulk created",
        DRAFT_ORDER_CREATED: "Draft order created",
        DRAFT_ORDER_UPDATED: "Draft order updated",
        DRAFT_ORDER_DELETED: "Draft order deleted",
        SALE_CREATED: "Sale created",
        SALE_UPDATED: "Sale updated",
        SALE_DELETED: "Sale deleted",
        SALE_TOGGLE: "Sale toggle",
        INVOICE_REQUESTED: "Invoice requested",
        INVOICE_DELETED: "Invoice deleted",
        INVOICE_SENT: "Invoice sent",
        CUSTOMER_CREATED: "Customer created",
        CUSTOMER_UPDATED: "Customer updated",
        CUSTOMER_DELETED: "Customer deleted",
        CUSTOMER_METADATA_UPDATED: "Customer metadata updated",
        COLLECTION_CREATED: "Collection created",
        COLLECTION_UPDATED: "Collection updated",
        COLLECTION_DELETED: "Collection deleted",
        COLLECTION_METADATA_UPDATED: "Collection metadata updated",
        PRODUCT_CREATED: "Product created",
        PRODUCT_UPDATED: "Product updated",
        PRODUCT_DELETED: "Product deleted",
        PRODUCT_MEDIA_CREATED: "Product media created",
        PRODUCT_MEDIA_UPDATED: "Product media updated",
        PRODUCT_MEDIA_DELETED: "Product media deleted",
        PRODUCT_METADATA_UPDATED: "Product metadata updated",
        PRODUCT_VARIANT_CREATED: "Product variant created",
        PRODUCT_VARIANT_UPDATED: "Product variant updated",
        PRODUCT_VARIANT_DELETED: "Product variant deleted",
        PRODUCT_VARIANT_METADATA_UPDATED: "Product variant metadata updated",
        PRODUCT_VARIANT_OUT_OF_STOCK: "Product variant stock changed",
        PRODUCT_VARIANT_BACK_IN_STOCK: "Product variant back in stock",
        PRODUCT_VARIANT_STOCK_UPDATED: "Product variant stock updated",
        CHECKOUT_CREATED: "Checkout created",
        CHECKOUT_UPDATED: "Checkout updated",
        CHECKOUT_FULLY_PAID: "Checkout fully paid",
        CHECKOUT_METADATA_UPDATED: "Checkout metadata updated",
        FULFILLMENT_CREATED: "Fulfillment created",
        FULFILLMENT_CANCELED: "Fulfillment cancelled",
        FULFILLMENT_APPROVED: "Fulfillment approved",
        FULFILLMENT_METADATA_UPDATED: "Fulfillment metadata updated",
        NOTIFY_USER: "Notify user",
        PAGE_CREATED: "Page Created",
        PAGE_UPDATED: "Page Updated",
        PAGE_DELETED: "Page Deleted",
        PAGE_TYPE_CREATED: "Page type created",
        PAGE_TYPE_UPDATED: "Page type updated",
        PAGE_TYPE_DELETED: "Page type deleted",
        PERMISSION_GROUP_CREATED: "Permission group created",
        PERMISSION_GROUP_UPDATED: "Permission group updated",
        PERMISSION_GROUP_DELETED: "Permission group deleted",
        SHIPPING_PRICE_CREATED: "Shipping price created",
        SHIPPING_PRICE_UPDATED: "Shipping price updated",
        SHIPPING_PRICE_DELETED: "Shipping price deleted",
        SHIPPING_ZONE_CREATED: "Shipping zone created",
        SHIPPING_ZONE_UPDATED: "Shipping zone updated",
        SHIPPING_ZONE_DELETED: "Shipping zone deleted",
        SHIPPING_ZONE_METADATA_UPDATED: "Shipping zone metadata updated",
        STAFF_CREATED: "Staff created",
        STAFF_UPDATED: "Staff updated",
        STAFF_DELETED: "Staff deleted",
        TRANSACTION_ITEM_METADATA_UPDATED: "Transaction item metadata updated",
        TRANSLATION_CREATED: "Create translation",
        TRANSLATION_UPDATED: "Update translation",
        WAREHOUSE_CREATED: "Warehouse created",
        WAREHOUSE_UPDATED: "Warehouse updated",
        WAREHOUSE_DELETED: "Warehouse deleted",
        WAREHOUSE_METADATA_UPDATED: "Warehouse metadata updated",
        VOUCHER_CREATED: "Voucher created",
        VOUCHER_UPDATED: "Voucher updated",
        VOUCHER_DELETED: "Voucher deleted",
        VOUCHER_METADATA_UPDATED: "Voucher metadata updated",
        OBSERVABILITY: "Observability",
        THUMBNAIL_CREATED: "Thumbnail created",
    }

    CHOICES = [
        (ANY, DISPLAY_LABELS[ANY]),
        (
            ACCOUNT_CONFIRMATION_REQUESTED,
            DISPLAY_LABELS[ACCOUNT_CONFIRMATION_REQUESTED],
        ),
        (
            ACCOUNT_CHANGE_EMAIL_REQUESTED,
            DISPLAY_LABELS[ACCOUNT_CHANGE_EMAIL_REQUESTED],
        ),
        (ACCOUNT_DELETE_REQUESTED, DISPLAY_LABELS[ACCOUNT_DELETE_REQUESTED]),
        (ADDRESS_CREATED, DISPLAY_LABELS[ADDRESS_CREATED]),
        (ADDRESS_UPDATED, DISPLAY_LABELS[ADDRESS_UPDATED]),
        (ADDRESS_DELETED, DISPLAY_LABELS[ADDRESS_DELETED]),
        (APP_INSTALLED, DISPLAY_LABELS[APP_INSTALLED]),
        (APP_UPDATED, DISPLAY_LABELS[APP_UPDATED]),
        (APP_DELETED, DISPLAY_LABELS[APP_DELETED]),
        (APP_STATUS_CHANGED, DISPLAY_LABELS[APP_STATUS_CHANGED]),
        (ATTRIBUTE_CREATED, DISPLAY_LABELS[ATTRIBUTE_CREATED]),
        (ATTRIBUTE_UPDATED, DISPLAY_LABELS[ATTRIBUTE_UPDATED]),
        (ATTRIBUTE_DELETED, DISPLAY_LABELS[ATTRIBUTE_DELETED]),
        (ATTRIBUTE_VALUE_CREATED, DISPLAY_LABELS[ATTRIBUTE_VALUE_CREATED]),
        (ATTRIBUTE_VALUE_UPDATED, DISPLAY_LABELS[ATTRIBUTE_VALUE_UPDATED]),
        (ATTRIBUTE_VALUE_DELETED, DISPLAY_LABELS[ATTRIBUTE_VALUE_DELETED]),
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
        (GIFT_CARD_SENT, DISPLAY_LABELS[GIFT_CARD_SENT]),
        (GIFT_CARD_STATUS_CHANGED, DISPLAY_LABELS[GIFT_CARD_STATUS_CHANGED]),
        (GIFT_CARD_METADATA_UPDATED, DISPLAY_LABELS[GIFT_CARD_METADATA_UPDATED]),
        (MENU_CREATED, DISPLAY_LABELS[MENU_CREATED]),
        (MENU_UPDATED, DISPLAY_LABELS[MENU_UPDATED]),
        (MENU_DELETED, DISPLAY_LABELS[MENU_DELETED]),
        (MENU_ITEM_CREATED, DISPLAY_LABELS[MENU_ITEM_CREATED]),
        (MENU_ITEM_UPDATED, DISPLAY_LABELS[MENU_ITEM_UPDATED]),
        (MENU_ITEM_DELETED, DISPLAY_LABELS[MENU_ITEM_DELETED]),
        (ORDER_CREATED, DISPLAY_LABELS[ORDER_CREATED]),
        (ORDER_CONFIRMED, DISPLAY_LABELS[ORDER_CONFIRMED]),
        (ORDER_PAID, DISPLAY_LABELS[ORDER_PAID]),
        (ORDER_FULLY_PAID, DISPLAY_LABELS[ORDER_FULLY_PAID]),
        (ORDER_REFUNDED, DISPLAY_LABELS[ORDER_REFUNDED]),
        (ORDER_FULLY_REFUNDED, DISPLAY_LABELS[ORDER_FULLY_REFUNDED]),
        (ORDER_UPDATED, DISPLAY_LABELS[ORDER_UPDATED]),
        (ORDER_CANCELLED, DISPLAY_LABELS[ORDER_CANCELLED]),
        (ORDER_EXPIRED, DISPLAY_LABELS[ORDER_EXPIRED]),
        (ORDER_FULFILLED, DISPLAY_LABELS[ORDER_FULFILLED]),
        (ORDER_METADATA_UPDATED, DISPLAY_LABELS[ORDER_METADATA_UPDATED]),
        (ORDER_BULK_CREATED, DISPLAY_LABELS[ORDER_BULK_CREATED]),
        (DRAFT_ORDER_CREATED, DISPLAY_LABELS[DRAFT_ORDER_CREATED]),
        (DRAFT_ORDER_UPDATED, DISPLAY_LABELS[DRAFT_ORDER_UPDATED]),
        (DRAFT_ORDER_DELETED, DISPLAY_LABELS[DRAFT_ORDER_DELETED]),
        (SALE_CREATED, DISPLAY_LABELS[SALE_CREATED]),
        (SALE_UPDATED, DISPLAY_LABELS[SALE_UPDATED]),
        (SALE_DELETED, DISPLAY_LABELS[SALE_DELETED]),
        (SALE_TOGGLE, DISPLAY_LABELS[SALE_TOGGLE]),
        (INVOICE_REQUESTED, DISPLAY_LABELS[INVOICE_REQUESTED]),
        (INVOICE_DELETED, DISPLAY_LABELS[INVOICE_DELETED]),
        (INVOICE_SENT, DISPLAY_LABELS[INVOICE_SENT]),
        (CUSTOMER_CREATED, DISPLAY_LABELS[CUSTOMER_CREATED]),
        (CUSTOMER_UPDATED, DISPLAY_LABELS[CUSTOMER_UPDATED]),
        (CUSTOMER_DELETED, DISPLAY_LABELS[CUSTOMER_DELETED]),
        (CUSTOMER_METADATA_UPDATED, DISPLAY_LABELS[CUSTOMER_METADATA_UPDATED]),
        (COLLECTION_CREATED, DISPLAY_LABELS[COLLECTION_CREATED]),
        (COLLECTION_UPDATED, DISPLAY_LABELS[COLLECTION_UPDATED]),
        (COLLECTION_DELETED, DISPLAY_LABELS[COLLECTION_DELETED]),
        (COLLECTION_METADATA_UPDATED, DISPLAY_LABELS[COLLECTION_METADATA_UPDATED]),
        (PRODUCT_CREATED, DISPLAY_LABELS[PRODUCT_CREATED]),
        (PRODUCT_UPDATED, DISPLAY_LABELS[PRODUCT_UPDATED]),
        (PRODUCT_DELETED, DISPLAY_LABELS[PRODUCT_DELETED]),
        (PRODUCT_MEDIA_CREATED, DISPLAY_LABELS[PRODUCT_MEDIA_CREATED]),
        (PRODUCT_MEDIA_UPDATED, DISPLAY_LABELS[PRODUCT_MEDIA_UPDATED]),
        (PRODUCT_MEDIA_DELETED, DISPLAY_LABELS[PRODUCT_MEDIA_DELETED]),
        (PRODUCT_METADATA_UPDATED, DISPLAY_LABELS[PRODUCT_METADATA_UPDATED]),
        (PRODUCT_VARIANT_CREATED, DISPLAY_LABELS[PRODUCT_VARIANT_CREATED]),
        (PRODUCT_VARIANT_UPDATED, DISPLAY_LABELS[PRODUCT_VARIANT_UPDATED]),
        (PRODUCT_VARIANT_DELETED, DISPLAY_LABELS[PRODUCT_VARIANT_DELETED]),
        (PRODUCT_VARIANT_OUT_OF_STOCK, DISPLAY_LABELS[PRODUCT_VARIANT_OUT_OF_STOCK]),
        (PRODUCT_VARIANT_BACK_IN_STOCK, DISPLAY_LABELS[PRODUCT_VARIANT_BACK_IN_STOCK]),
        (PRODUCT_VARIANT_STOCK_UPDATED, DISPLAY_LABELS[PRODUCT_VARIANT_STOCK_UPDATED]),
        (
            PRODUCT_VARIANT_METADATA_UPDATED,
            DISPLAY_LABELS[PRODUCT_VARIANT_METADATA_UPDATED],
        ),
        (CHECKOUT_CREATED, DISPLAY_LABELS[CHECKOUT_CREATED]),
        (CHECKOUT_UPDATED, DISPLAY_LABELS[CHECKOUT_UPDATED]),
        (CHECKOUT_FULLY_PAID, DISPLAY_LABELS[CHECKOUT_FULLY_PAID]),
        (CHECKOUT_METADATA_UPDATED, DISPLAY_LABELS[CHECKOUT_METADATA_UPDATED]),
        (FULFILLMENT_CREATED, DISPLAY_LABELS[FULFILLMENT_CREATED]),
        (FULFILLMENT_CANCELED, DISPLAY_LABELS[FULFILLMENT_CANCELED]),
        (FULFILLMENT_APPROVED, DISPLAY_LABELS[FULFILLMENT_APPROVED]),
        (FULFILLMENT_METADATA_UPDATED, DISPLAY_LABELS[FULFILLMENT_METADATA_UPDATED]),
        (NOTIFY_USER, DISPLAY_LABELS[NOTIFY_USER]),
        (PAGE_CREATED, DISPLAY_LABELS[PAGE_CREATED]),
        (PAGE_UPDATED, DISPLAY_LABELS[PAGE_UPDATED]),
        (PAGE_DELETED, DISPLAY_LABELS[PAGE_DELETED]),
        (PAGE_TYPE_CREATED, DISPLAY_LABELS[PAGE_TYPE_CREATED]),
        (PAGE_TYPE_UPDATED, DISPLAY_LABELS[PAGE_TYPE_UPDATED]),
        (PAGE_TYPE_DELETED, DISPLAY_LABELS[PAGE_TYPE_DELETED]),
        (PERMISSION_GROUP_CREATED, DISPLAY_LABELS[PERMISSION_GROUP_CREATED]),
        (PERMISSION_GROUP_UPDATED, DISPLAY_LABELS[PERMISSION_GROUP_UPDATED]),
        (PERMISSION_GROUP_DELETED, DISPLAY_LABELS[PERMISSION_GROUP_DELETED]),
        (SHIPPING_PRICE_CREATED, DISPLAY_LABELS[SHIPPING_PRICE_CREATED]),
        (SHIPPING_PRICE_UPDATED, DISPLAY_LABELS[SHIPPING_PRICE_UPDATED]),
        (SHIPPING_PRICE_DELETED, DISPLAY_LABELS[SHIPPING_PRICE_DELETED]),
        (SHIPPING_ZONE_CREATED, DISPLAY_LABELS[SHIPPING_ZONE_CREATED]),
        (SHIPPING_ZONE_UPDATED, DISPLAY_LABELS[SHIPPING_ZONE_UPDATED]),
        (SHIPPING_ZONE_DELETED, DISPLAY_LABELS[SHIPPING_ZONE_DELETED]),
        (
            SHIPPING_ZONE_METADATA_UPDATED,
            DISPLAY_LABELS[SHIPPING_ZONE_METADATA_UPDATED],
        ),
        (STAFF_CREATED, DISPLAY_LABELS[STAFF_CREATED]),
        (STAFF_UPDATED, DISPLAY_LABELS[STAFF_UPDATED]),
        (STAFF_DELETED, DISPLAY_LABELS[STAFF_DELETED]),
        (
            TRANSACTION_ITEM_METADATA_UPDATED,
            DISPLAY_LABELS[TRANSACTION_ITEM_METADATA_UPDATED],
        ),
        (TRANSLATION_CREATED, DISPLAY_LABELS[TRANSLATION_CREATED]),
        (TRANSLATION_UPDATED, DISPLAY_LABELS[TRANSLATION_UPDATED]),
        (WAREHOUSE_CREATED, DISPLAY_LABELS[WAREHOUSE_CREATED]),
        (WAREHOUSE_UPDATED, DISPLAY_LABELS[WAREHOUSE_UPDATED]),
        (WAREHOUSE_DELETED, DISPLAY_LABELS[WAREHOUSE_DELETED]),
        (WAREHOUSE_METADATA_UPDATED, DISPLAY_LABELS[WAREHOUSE_METADATA_UPDATED]),
        (VOUCHER_CREATED, DISPLAY_LABELS[VOUCHER_CREATED]),
        (VOUCHER_UPDATED, DISPLAY_LABELS[VOUCHER_UPDATED]),
        (VOUCHER_DELETED, DISPLAY_LABELS[VOUCHER_DELETED]),
        (VOUCHER_METADATA_UPDATED, DISPLAY_LABELS[VOUCHER_METADATA_UPDATED]),
        (OBSERVABILITY, DISPLAY_LABELS[OBSERVABILITY]),
        (THUMBNAIL_CREATED, DISPLAY_LABELS[THUMBNAIL_CREATED]),
    ]

    ALL = [event[0] for event in CHOICES]

    PERMISSIONS = {
        ACCOUNT_CONFIRMATION_REQUESTED: AccountPermissions.MANAGE_USERS,
        ACCOUNT_CHANGE_EMAIL_REQUESTED: AccountPermissions.MANAGE_USERS,
        ACCOUNT_DELETE_REQUESTED: AccountPermissions.MANAGE_USERS,
        ADDRESS_CREATED: AccountPermissions.MANAGE_USERS,
        ADDRESS_UPDATED: AccountPermissions.MANAGE_USERS,
        ADDRESS_DELETED: AccountPermissions.MANAGE_USERS,
        APP_INSTALLED: AppPermission.MANAGE_APPS,
        APP_UPDATED: AppPermission.MANAGE_APPS,
        APP_DELETED: AppPermission.MANAGE_APPS,
        APP_STATUS_CHANGED: AppPermission.MANAGE_APPS,
        ATTRIBUTE_CREATED: None,
        ATTRIBUTE_UPDATED: None,
        ATTRIBUTE_DELETED: None,
        ATTRIBUTE_VALUE_CREATED: None,
        ATTRIBUTE_VALUE_UPDATED: None,
        ATTRIBUTE_VALUE_DELETED: None,
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
        GIFT_CARD_SENT: GiftcardPermissions.MANAGE_GIFT_CARD,
        GIFT_CARD_STATUS_CHANGED: GiftcardPermissions.MANAGE_GIFT_CARD,
        GIFT_CARD_METADATA_UPDATED: GiftcardPermissions.MANAGE_GIFT_CARD,
        MENU_CREATED: MenuPermissions.MANAGE_MENUS,
        MENU_UPDATED: MenuPermissions.MANAGE_MENUS,
        MENU_DELETED: MenuPermissions.MANAGE_MENUS,
        MENU_ITEM_CREATED: MenuPermissions.MANAGE_MENUS,
        MENU_ITEM_UPDATED: MenuPermissions.MANAGE_MENUS,
        MENU_ITEM_DELETED: MenuPermissions.MANAGE_MENUS,
        ORDER_CREATED: OrderPermissions.MANAGE_ORDERS,
        ORDER_CONFIRMED: OrderPermissions.MANAGE_ORDERS,
        ORDER_PAID: OrderPermissions.MANAGE_ORDERS,
        ORDER_FULLY_PAID: OrderPermissions.MANAGE_ORDERS,
        ORDER_REFUNDED: OrderPermissions.MANAGE_ORDERS,
        ORDER_FULLY_REFUNDED: OrderPermissions.MANAGE_ORDERS,
        ORDER_UPDATED: OrderPermissions.MANAGE_ORDERS,
        ORDER_CANCELLED: OrderPermissions.MANAGE_ORDERS,
        ORDER_EXPIRED: OrderPermissions.MANAGE_ORDERS,
        ORDER_FULFILLED: OrderPermissions.MANAGE_ORDERS,
        ORDER_METADATA_UPDATED: OrderPermissions.MANAGE_ORDERS,
        ORDER_BULK_CREATED: OrderPermissions.MANAGE_ORDERS,
        DRAFT_ORDER_CREATED: OrderPermissions.MANAGE_ORDERS,
        DRAFT_ORDER_DELETED: OrderPermissions.MANAGE_ORDERS,
        DRAFT_ORDER_UPDATED: OrderPermissions.MANAGE_ORDERS,
        SALE_CREATED: DiscountPermissions.MANAGE_DISCOUNTS,
        SALE_UPDATED: DiscountPermissions.MANAGE_DISCOUNTS,
        SALE_DELETED: DiscountPermissions.MANAGE_DISCOUNTS,
        SALE_TOGGLE: DiscountPermissions.MANAGE_DISCOUNTS,
        INVOICE_REQUESTED: OrderPermissions.MANAGE_ORDERS,
        INVOICE_DELETED: OrderPermissions.MANAGE_ORDERS,
        INVOICE_SENT: OrderPermissions.MANAGE_ORDERS,
        CUSTOMER_CREATED: AccountPermissions.MANAGE_USERS,
        CUSTOMER_UPDATED: AccountPermissions.MANAGE_USERS,
        CUSTOMER_DELETED: AccountPermissions.MANAGE_USERS,
        CUSTOMER_METADATA_UPDATED: AccountPermissions.MANAGE_USERS,
        COLLECTION_CREATED: ProductPermissions.MANAGE_PRODUCTS,
        COLLECTION_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        COLLECTION_DELETED: ProductPermissions.MANAGE_PRODUCTS,
        COLLECTION_METADATA_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_CREATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_DELETED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_METADATA_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_MEDIA_CREATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_MEDIA_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_MEDIA_DELETED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_CREATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_DELETED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_METADATA_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_BACK_IN_STOCK: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_OUT_OF_STOCK: ProductPermissions.MANAGE_PRODUCTS,
        PRODUCT_VARIANT_STOCK_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        CHECKOUT_CREATED: CheckoutPermissions.MANAGE_CHECKOUTS,
        CHECKOUT_UPDATED: CheckoutPermissions.MANAGE_CHECKOUTS,
        CHECKOUT_FULLY_PAID: CheckoutPermissions.MANAGE_CHECKOUTS,
        CHECKOUT_METADATA_UPDATED: CheckoutPermissions.MANAGE_CHECKOUTS,
        FULFILLMENT_CREATED: OrderPermissions.MANAGE_ORDERS,
        FULFILLMENT_CANCELED: OrderPermissions.MANAGE_ORDERS,
        FULFILLMENT_APPROVED: OrderPermissions.MANAGE_ORDERS,
        FULFILLMENT_METADATA_UPDATED: OrderPermissions.MANAGE_ORDERS,
        NOTIFY_USER: AccountPermissions.MANAGE_USERS,
        PAGE_CREATED: PagePermissions.MANAGE_PAGES,
        PAGE_UPDATED: PagePermissions.MANAGE_PAGES,
        PAGE_DELETED: PagePermissions.MANAGE_PAGES,
        PAGE_TYPE_CREATED: PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
        PAGE_TYPE_UPDATED: PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
        PAGE_TYPE_DELETED: PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
        PERMISSION_GROUP_CREATED: AccountPermissions.MANAGE_STAFF,
        PERMISSION_GROUP_UPDATED: AccountPermissions.MANAGE_STAFF,
        PERMISSION_GROUP_DELETED: AccountPermissions.MANAGE_STAFF,
        SHIPPING_PRICE_CREATED: ShippingPermissions.MANAGE_SHIPPING,
        SHIPPING_PRICE_UPDATED: ShippingPermissions.MANAGE_SHIPPING,
        SHIPPING_PRICE_DELETED: ShippingPermissions.MANAGE_SHIPPING,
        SHIPPING_ZONE_CREATED: ShippingPermissions.MANAGE_SHIPPING,
        SHIPPING_ZONE_UPDATED: ShippingPermissions.MANAGE_SHIPPING,
        SHIPPING_ZONE_DELETED: ShippingPermissions.MANAGE_SHIPPING,
        SHIPPING_ZONE_METADATA_UPDATED: ShippingPermissions.MANAGE_SHIPPING,
        STAFF_CREATED: AccountPermissions.MANAGE_STAFF,
        STAFF_UPDATED: AccountPermissions.MANAGE_STAFF,
        STAFF_DELETED: AccountPermissions.MANAGE_STAFF,
        TRANSACTION_ITEM_METADATA_UPDATED: PaymentPermissions.HANDLE_PAYMENTS,
        TRANSLATION_CREATED: SitePermissions.MANAGE_TRANSLATIONS,
        TRANSLATION_UPDATED: SitePermissions.MANAGE_TRANSLATIONS,
        VOUCHER_CREATED: DiscountPermissions.MANAGE_DISCOUNTS,
        VOUCHER_UPDATED: DiscountPermissions.MANAGE_DISCOUNTS,
        VOUCHER_DELETED: DiscountPermissions.MANAGE_DISCOUNTS,
        VOUCHER_METADATA_UPDATED: DiscountPermissions.MANAGE_DISCOUNTS,
        WAREHOUSE_CREATED: ProductPermissions.MANAGE_PRODUCTS,
        WAREHOUSE_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        WAREHOUSE_DELETED: ProductPermissions.MANAGE_PRODUCTS,
        WAREHOUSE_METADATA_UPDATED: ProductPermissions.MANAGE_PRODUCTS,
        OBSERVABILITY: AppPermission.MANAGE_OBSERVABILITY,
        THUMBNAIL_CREATED: ProductPermissions.MANAGE_PRODUCTS,
    }


class WebhookEventSyncType:
    PAYMENT_LIST_GATEWAYS = "payment_list_gateways"
    PAYMENT_AUTHORIZE = "payment_authorize"
    PAYMENT_CAPTURE = "payment_capture"
    PAYMENT_REFUND = "payment_refund"
    PAYMENT_VOID = "payment_void"
    PAYMENT_CONFIRM = "payment_confirm"
    PAYMENT_PROCESS = "payment_process"

    CHECKOUT_CALCULATE_TAXES = "checkout_calculate_taxes"
    ORDER_CALCULATE_TAXES = "order_calculate_taxes"

    TRANSACTION_CHARGE_REQUESTED = "transaction_charge_requested"
    TRANSACTION_REFUND_REQUESTED = "transaction_refund_requested"
    TRANSACTION_CANCELATION_REQUESTED = "transaction_cancelation_requested"

    SHIPPING_LIST_METHODS_FOR_CHECKOUT = "shipping_list_methods_for_checkout"
    CHECKOUT_FILTER_SHIPPING_METHODS = "checkout_filter_shipping_methods"
    ORDER_FILTER_SHIPPING_METHODS = "order_filter_shipping_methods"

    PAYMENT_GATEWAY_INITIALIZE_SESSION = "payment_gateway_initialize_session"
    TRANSACTION_INITIALIZE_SESSION = "transaction_initialize_session"
    TRANSACTION_PROCESS_SESSION = "transaction_process_session"

    DISPLAY_LABELS = {
        PAYMENT_AUTHORIZE: "Authorize payment",
        PAYMENT_CAPTURE: "Capture payment",
        PAYMENT_CONFIRM: "Confirm payment",
        PAYMENT_LIST_GATEWAYS: "List payment gateways",
        PAYMENT_PROCESS: "Process payment",
        PAYMENT_REFUND: "Refund payment",
        PAYMENT_VOID: "Void payment",
        TRANSACTION_CHARGE_REQUESTED: "Transaction charge requested",
        TRANSACTION_CANCELATION_REQUESTED: "Transaction cancelation requested",
        TRANSACTION_REFUND_REQUESTED: "Transaction refund requested",
        CHECKOUT_CALCULATE_TAXES: "Checkout calculate taxes",
        ORDER_CALCULATE_TAXES: "Order calculate taxes",
        SHIPPING_LIST_METHODS_FOR_CHECKOUT: "Shipping list methods for checkout",
        ORDER_FILTER_SHIPPING_METHODS: "Filter order shipping methods",
        CHECKOUT_FILTER_SHIPPING_METHODS: "Filter checkout shipping methods",
        PAYMENT_GATEWAY_INITIALIZE_SESSION: "Initialize payment gateway session",
        TRANSACTION_INITIALIZE_SESSION: "Initialize transaction session",
        TRANSACTION_PROCESS_SESSION: "Process transaction session",
    }

    CHOICES = [
        (PAYMENT_AUTHORIZE, DISPLAY_LABELS[PAYMENT_AUTHORIZE]),
        (PAYMENT_CAPTURE, DISPLAY_LABELS[PAYMENT_CAPTURE]),
        (PAYMENT_CONFIRM, DISPLAY_LABELS[PAYMENT_CONFIRM]),
        (PAYMENT_LIST_GATEWAYS, DISPLAY_LABELS[PAYMENT_LIST_GATEWAYS]),
        (PAYMENT_PROCESS, DISPLAY_LABELS[PAYMENT_PROCESS]),
        (PAYMENT_REFUND, DISPLAY_LABELS[PAYMENT_REFUND]),
        (PAYMENT_VOID, DISPLAY_LABELS[PAYMENT_VOID]),
        (TRANSACTION_CHARGE_REQUESTED, DISPLAY_LABELS[TRANSACTION_CHARGE_REQUESTED]),
        (TRANSACTION_REFUND_REQUESTED, DISPLAY_LABELS[TRANSACTION_REFUND_REQUESTED]),
        (
            TRANSACTION_CANCELATION_REQUESTED,
            DISPLAY_LABELS[TRANSACTION_CANCELATION_REQUESTED],
        ),
        (CHECKOUT_CALCULATE_TAXES, DISPLAY_LABELS[CHECKOUT_CALCULATE_TAXES]),
        (ORDER_CALCULATE_TAXES, DISPLAY_LABELS[ORDER_CALCULATE_TAXES]),
        (
            SHIPPING_LIST_METHODS_FOR_CHECKOUT,
            DISPLAY_LABELS[SHIPPING_LIST_METHODS_FOR_CHECKOUT],
        ),
        (ORDER_FILTER_SHIPPING_METHODS, DISPLAY_LABELS[ORDER_FILTER_SHIPPING_METHODS]),
        (
            CHECKOUT_FILTER_SHIPPING_METHODS,
            DISPLAY_LABELS[CHECKOUT_FILTER_SHIPPING_METHODS],
        ),
        (
            PAYMENT_GATEWAY_INITIALIZE_SESSION,
            DISPLAY_LABELS[PAYMENT_GATEWAY_INITIALIZE_SESSION],
        ),
        (
            TRANSACTION_INITIALIZE_SESSION,
            DISPLAY_LABELS[TRANSACTION_INITIALIZE_SESSION],
        ),
        (TRANSACTION_PROCESS_SESSION, DISPLAY_LABELS[TRANSACTION_PROCESS_SESSION]),
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

    # Events that are used only in the mutation logic can be excluded from the
    # circular query check.
    ALLOWED_IN_CIRCULAR_QUERY = [
        PAYMENT_GATEWAY_INITIALIZE_SESSION,
        TRANSACTION_INITIALIZE_SESSION,
        TRANSACTION_PROCESS_SESSION,
        TRANSACTION_CHARGE_REQUESTED,
        TRANSACTION_REFUND_REQUESTED,
        TRANSACTION_CANCELATION_REQUESTED,
    ]

    PERMISSIONS = {
        PAYMENT_AUTHORIZE: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_CAPTURE: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_CONFIRM: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_LIST_GATEWAYS: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_PROCESS: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_REFUND: PaymentPermissions.HANDLE_PAYMENTS,
        PAYMENT_VOID: PaymentPermissions.HANDLE_PAYMENTS,
        TRANSACTION_REFUND_REQUESTED: PaymentPermissions.HANDLE_PAYMENTS,
        TRANSACTION_CANCELATION_REQUESTED: PaymentPermissions.HANDLE_PAYMENTS,
        TRANSACTION_CHARGE_REQUESTED: PaymentPermissions.HANDLE_PAYMENTS,
        CHECKOUT_CALCULATE_TAXES: CheckoutPermissions.HANDLE_TAXES,
        ORDER_CALCULATE_TAXES: CheckoutPermissions.HANDLE_TAXES,
        SHIPPING_LIST_METHODS_FOR_CHECKOUT: ShippingPermissions.MANAGE_SHIPPING,
        ORDER_FILTER_SHIPPING_METHODS: OrderPermissions.MANAGE_ORDERS,
        CHECKOUT_FILTER_SHIPPING_METHODS: CheckoutPermissions.MANAGE_CHECKOUTS,
        PAYMENT_GATEWAY_INITIALIZE_SESSION: PaymentPermissions.HANDLE_PAYMENTS,
        TRANSACTION_INITIALIZE_SESSION: PaymentPermissions.HANDLE_PAYMENTS,
        TRANSACTION_PROCESS_SESSION: PaymentPermissions.HANDLE_PAYMENTS,
    }
