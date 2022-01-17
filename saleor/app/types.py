class AppType:
    LOCAL = "local"
    THIRDPARTY = "thirdparty"

    CHOICES = [(LOCAL, "local"), (THIRDPARTY, "thirdparty")]


class AppExtensionView:
    """All available places where app's iframe can be mounted.

    PRODUCT - app's extension will be mounted in product section
    ALL - app's extension will be mounted in all views
    """

    PRODUCT = "product"
    ALL = "all"

    CHOICES = [(PRODUCT, "product"), (ALL, "all")]


class AppExtensionType:
    """All available types where app's iframe can be mounted.

    OVERVIEW - app's extension will be mounted on list view.
    DETAILS - app's extension will be mounted on detail view
    NAVIGATION - app's extension will be mounted on navigation
    """

    OVERVIEW = "overview"
    DETAILS = "details"
    NAVIGATION = "navigation"

    CHOICES = [(OVERVIEW, "overview"), (DETAILS, "details"), (NAVIGATION, "navigation")]


class AppExtensionOpenAs:
    """All available ways of opening an app extension.

    POPUP - app's extension will be mounted as a popup window
    APP_PAGE - redirect to app's page
    """

    POPUP = "popup"
    APP_PAGE = "app_page"

    CHOICES = [(POPUP, "popup"), (APP_PAGE, "app_page")]


class AppExtensionTarget:
    """All available places where app's iframe can be mounted.

    MORE_ACTIONS - more actions button
    CREATE - create button
    CATALOG - catalog section on navigation bar
    ORDERS - orders section on navigation bar
    CUSTOMERS - customers section on navigation bar
    DISCOUNTS - discounts section on navigation bar
    TRANSLATION - translations section on navigation bar
    PAGES - pages section on navigation bar
    """

    MORE_ACTIONS = "more_actions"
    CREATE = "create"
    CATALOG = "catalog"
    ORDERS = "orders"
    CUSTOMERS = "customers"
    DISCOUNTS = "discounts"
    TRANSLATIONS = "translations"
    PAGES = "pages"

    CHOICES = [
        (MORE_ACTIONS, "more_actions"),
        (CREATE, "create"),
        (CATALOG, "catalog"),
        (ORDERS, "orders"),
        (CUSTOMERS, "customers"),
        (DISCOUNTS, "discounts"),
        (TRANSLATIONS, "translations"),
        (PAGES, "pages"),
    ]
