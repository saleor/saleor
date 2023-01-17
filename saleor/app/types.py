class AppType:
    LOCAL = "local"
    THIRDPARTY = "thirdparty"

    CHOICES = [(LOCAL, "local"), (THIRDPARTY, "thirdparty")]


class AppExtensionMount:
    """All places where app extension can be mounted."""

    CUSTOMER_OVERVIEW_CREATE = "customer_overview_create"
    CUSTOMER_OVERVIEW_MORE_ACTIONS = "customer_overview_more_actions"
    CUSTOMER_DETAILS_MORE_ACTIONS = "customer_details_more_actions"

    PRODUCT_OVERVIEW_CREATE = "product_overview_create"
    PRODUCT_OVERVIEW_MORE_ACTIONS = "product_overview_more_actions"
    PRODUCT_DETAILS_MORE_ACTIONS = "product_details_more_actions"

    NAVIGATION_CATALOG = "navigation_catalog"
    NAVIGATION_ORDERS = "navigation_orders"
    NAVIGATION_CUSTOMERS = "navigation_customers"
    NAVIGATION_DISCOUNTS = "navigation_discounts"
    NAVIGATION_TRANSLATIONS = "navigation_translations"
    NAVIGATION_PAGES = "navigation_pages"

    ORDER_DETAILS_MORE_ACTIONS = "order_details_more_actions"
    ORDER_OVERVIEW_CREATE = "order_overview_create"
    ORDER_OVERVIEW_MORE_ACTIONS = "order_overview_more_actions"

    CHOICES = [
        (CUSTOMER_OVERVIEW_CREATE, "customer_overview_create"),
        (CUSTOMER_OVERVIEW_MORE_ACTIONS, "customer_overview_more_actions"),
        (CUSTOMER_DETAILS_MORE_ACTIONS, "customer_details_more_actions"),
        (PRODUCT_OVERVIEW_CREATE, "product_overview_create"),
        (PRODUCT_OVERVIEW_MORE_ACTIONS, "product_overview_more_actions"),
        (PRODUCT_DETAILS_MORE_ACTIONS, "product_details_more_actions"),
        (NAVIGATION_CATALOG, "navigation_catalog"),
        (NAVIGATION_ORDERS, "navigation_orders"),
        (NAVIGATION_CUSTOMERS, "navigation_customers"),
        (NAVIGATION_DISCOUNTS, "navigation_discounts"),
        (NAVIGATION_TRANSLATIONS, "navigation_translations"),
        (NAVIGATION_PAGES, "navigation_pages"),
        (ORDER_DETAILS_MORE_ACTIONS, "order_details_more_actions"),
        (ORDER_OVERVIEW_CREATE, "order_overview_create"),
        (ORDER_OVERVIEW_MORE_ACTIONS, "order_overview_more_actions"),
    ]


class AppExtensionTarget:
    """All available ways of opening an app extension.

    POPUP - app's extension will be mounted as a popup window
    APP_PAGE - redirect to app's page
    """

    POPUP = "popup"
    APP_PAGE = "app_page"

    CHOICES = [(POPUP, "popup"), (APP_PAGE, "app_page")]
