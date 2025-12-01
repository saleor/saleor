class AppType:
    LOCAL = "local"
    THIRDPARTY = "thirdparty"

    CHOICES = [(LOCAL, "local"), (THIRDPARTY, "thirdparty")]


# Deprecated. Remove this enum - Saleor will use plain strings in tests, and the exact values are managed by the Dashboard
class DeprecatedAppExtensionMount:
    """All places where app extension can be mounted."""

    CATEGORY_OVERVIEW_CREATE = "category_overview_create"
    CATEGORY_OVERVIEW_MORE_ACTIONS = "category_overview_more_actions"
    CATEGORY_DETAILS_MORE_ACTIONS = "category_details_more_actions"

    COLLECTION_OVERVIEW_CREATE = "collection_overview_create"
    COLLECTION_OVERVIEW_MORE_ACTIONS = "collection_overview_more_actions"
    COLLECTION_DETAILS_MORE_ACTIONS = "collection_details_more_actions"
    COLLECTION_DETAILS_WIDGETS = "collection_details_widgets"

    GIFT_CARD_OVERVIEW_CREATE = "gift_card_overview_create"
    GIFT_CARD_OVERVIEW_MORE_ACTIONS = "gift_card_overview_more_actions"
    GIFT_CARD_DETAILS_MORE_ACTIONS = "gift_card_details_more_actions"
    GIFT_CARD_DETAILS_WIDGETS = "gift_card_details_widgets"

    CUSTOMER_OVERVIEW_CREATE = "customer_overview_create"
    CUSTOMER_OVERVIEW_MORE_ACTIONS = "customer_overview_more_actions"
    CUSTOMER_DETAILS_MORE_ACTIONS = "customer_details_more_actions"
    CUSTOMER_DETAILS_WIDGETS = "customer_details_widgets"

    PRODUCT_OVERVIEW_CREATE = "product_overview_create"
    PRODUCT_OVERVIEW_MORE_ACTIONS = "product_overview_more_actions"
    PRODUCT_DETAILS_MORE_ACTIONS = "product_details_more_actions"
    PRODUCT_DETAILS_WIDGETS = "product_details_widgets"

    NAVIGATION_CATALOG = "navigation_catalog"
    NAVIGATION_ORDERS = "navigation_orders"
    NAVIGATION_CUSTOMERS = "navigation_customers"
    NAVIGATION_DISCOUNTS = "navigation_discounts"
    NAVIGATION_TRANSLATIONS = "navigation_translations"
    NAVIGATION_PAGES = "navigation_pages"

    ORDER_DETAILS_MORE_ACTIONS = "order_details_more_actions"
    ORDER_OVERVIEW_CREATE = "order_overview_create"
    ORDER_OVERVIEW_MORE_ACTIONS = "order_overview_more_actions"
    ORDER_DETAILS_WIDGETS = "order_details_widgets"

    DRAFT_ORDER_DETAILS_MORE_ACTIONS = "draft_order_details_more_actions"
    DRAFT_ORDER_OVERVIEW_CREATE = "draft_order_overview_create"
    DRAFT_ORDER_OVERVIEW_MORE_ACTIONS = "draft_order_overview_more_actions"
    DRAFT_ORDER_DETAILS_WIDGETS = "draft_order_details_widgets"

    DISCOUNT_DETAILS_MORE_ACTIONS = "discount_details_more_actions"
    DISCOUNT_OVERVIEW_CREATE = "discount_overview_create"
    DISCOUNT_OVERVIEW_MORE_ACTIONS = "discount_overview_more_actions"

    VOUCHER_DETAILS_MORE_ACTIONS = "voucher_details_more_actions"
    VOUCHER_OVERVIEW_CREATE = "voucher_overview_create"
    VOUCHER_OVERVIEW_MORE_ACTIONS = "voucher_overview_more_actions"
    VOUCHER_DETAILS_WIDGETS = "voucher_details_widgets"

    PAGE_DETAILS_MORE_ACTIONS = "page_details_more_actions"
    PAGE_OVERVIEW_CREATE = "page_overview_create"
    PAGE_OVERVIEW_MORE_ACTIONS = "page_overview_more_actions"

    PAGE_TYPE_OVERVIEW_CREATE = "page_type_overview_create"
    PAGE_TYPE_OVERVIEW_MORE_ACTIONS = "page_type_overview_more_actions"
    PAGE_TYPE_DETAILS_MORE_ACTIONS = "page_type_details_more_actions"

    MENU_OVERVIEW_CREATE = "menu_overview_create"
    MENU_OVERVIEW_MORE_ACTIONS = "menu_overview_more_actions"
    MENU_DETAILS_MORE_ACTIONS = "menu_details_more_actions"

    TRANSLATIONS_MORE_ACTIONS = "translations_more_actions"

    CHOICES = [
        (CATEGORY_OVERVIEW_CREATE, "category_overview_create"),
        (CATEGORY_OVERVIEW_MORE_ACTIONS, "category_overview_more_actions"),
        (CATEGORY_DETAILS_MORE_ACTIONS, "category_details_more_actions"),
        (COLLECTION_OVERVIEW_CREATE, "collection_overview_create"),
        (COLLECTION_OVERVIEW_MORE_ACTIONS, "collection_overview_more_actions"),
        (COLLECTION_DETAILS_MORE_ACTIONS, "collection_details_more_actions"),
        (COLLECTION_DETAILS_WIDGETS, "collection_details_widgets"),
        (GIFT_CARD_OVERVIEW_CREATE, "gift_card_overview_create"),
        (GIFT_CARD_OVERVIEW_MORE_ACTIONS, "gift_card_overview_more_actions"),
        (GIFT_CARD_DETAILS_MORE_ACTIONS, "gift_card_details_more_actions"),
        (GIFT_CARD_DETAILS_WIDGETS, "gift_card_details_widgets"),
        (CUSTOMER_OVERVIEW_CREATE, "customer_overview_create"),
        (CUSTOMER_OVERVIEW_MORE_ACTIONS, "customer_overview_more_actions"),
        (CUSTOMER_DETAILS_MORE_ACTIONS, "customer_details_more_actions"),
        (CUSTOMER_DETAILS_WIDGETS, "customer_details_widgets"),
        (PRODUCT_OVERVIEW_CREATE, "product_overview_create"),
        (PRODUCT_OVERVIEW_MORE_ACTIONS, "product_overview_more_actions"),
        (PRODUCT_DETAILS_MORE_ACTIONS, "product_details_more_actions"),
        (PRODUCT_DETAILS_WIDGETS, "product_details_widgets"),
        (NAVIGATION_CATALOG, "navigation_catalog"),
        (NAVIGATION_ORDERS, "navigation_orders"),
        (NAVIGATION_CUSTOMERS, "navigation_customers"),
        (NAVIGATION_DISCOUNTS, "navigation_discounts"),
        (NAVIGATION_TRANSLATIONS, "navigation_translations"),
        (NAVIGATION_PAGES, "navigation_pages"),
        (ORDER_DETAILS_MORE_ACTIONS, "order_details_more_actions"),
        (ORDER_OVERVIEW_CREATE, "order_overview_create"),
        (ORDER_OVERVIEW_MORE_ACTIONS, "order_overview_more_actions"),
        (ORDER_DETAILS_WIDGETS, "order_details_widgets"),
        (DRAFT_ORDER_DETAILS_MORE_ACTIONS, "draft_order_details_more_actions"),
        (DRAFT_ORDER_OVERVIEW_CREATE, "draft_order_overview_create"),
        (DRAFT_ORDER_OVERVIEW_MORE_ACTIONS, "draft_order_overview_more_actions"),
        (DRAFT_ORDER_DETAILS_WIDGETS, "draft_order_details_widgets"),
        (DISCOUNT_DETAILS_MORE_ACTIONS, "discount_details_more_actions"),
        (DISCOUNT_OVERVIEW_CREATE, "discount_overview_create"),
        (DISCOUNT_OVERVIEW_MORE_ACTIONS, "discount_overview_more_actions"),
        (VOUCHER_DETAILS_MORE_ACTIONS, "voucher_details_more_actions"),
        (VOUCHER_OVERVIEW_CREATE, "voucher_overview_create"),
        (VOUCHER_OVERVIEW_MORE_ACTIONS, "voucher_overview_more_actions"),
        (VOUCHER_DETAILS_WIDGETS, "voucher_details_widgets"),
        (PAGE_DETAILS_MORE_ACTIONS, "page_details_more_actions"),
        (PAGE_OVERVIEW_CREATE, "page_overview_create"),
        (PAGE_OVERVIEW_MORE_ACTIONS, "page_overview_more_actions"),
        (PAGE_TYPE_OVERVIEW_CREATE, "page_type_overview_create"),
        (PAGE_TYPE_OVERVIEW_MORE_ACTIONS, "page_type_overview_more_actions"),
        (PAGE_TYPE_DETAILS_MORE_ACTIONS, "page_type_details_more_actions"),
        (MENU_OVERVIEW_CREATE, "menu_overview_create"),
        (MENU_OVERVIEW_MORE_ACTIONS, "menu_overview_more_actions"),
        (MENU_DETAILS_MORE_ACTIONS, "menu_details_more_actions"),
        (TRANSLATIONS_MORE_ACTIONS, "translations_more_actions"),
    ]


# Deprecated. Remove this enum - Saleor will use plain strings in tests, and the exact values are managed by the Dashboard
class DeprecatedAppExtensionTarget:
    """All available ways of opening an app extension.

    POPUP - app's extension will be mounted as a popup window
    APP_PAGE - redirect to app's page
    """

    POPUP = "popup"
    APP_PAGE = "app_page"
    NEW_TAB = "new_tab"
    WIDGET = "widget"

    CHOICES = [
        (POPUP, "popup"),
        (APP_PAGE, "app_page"),
        (NEW_TAB, "new_tab"),
        (WIDGET, "widget"),
    ]


# Deprecated. Remove this enum in 3.24, when this field is dropped from AppExtension model
class DeprecatedAppExtensionHttpMethod:
    """HTTP methods available for app extensions.

    Represents available HTTPS methods for frontend to work with extension (WIDGET and NEW_TAB)
    """

    GET = "GET"
    POST = "POST"

    CHOICES = [("GET", "GET"), ("POST", "POST")]


# We need special handling for popup - if it declares relative extension URL, resolver will stitch if with app URL
POPUP_EXTENSION_TARGET = "popup"

# In case of not provided, use the default value as a fallback
DEFAULT_APP_TARGET = POPUP_EXTENSION_TARGET
