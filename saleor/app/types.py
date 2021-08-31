class AppType:
    LOCAL = "local"
    THIRDPARTY = "thirdparty"

    CHOICES = [(LOCAL, "local"), (THIRDPARTY, "thirdparty")]


class AppExtensionView:
    """All available places where app's iframe can be mounted.

    PRODUCT - app's iframe will be mounted in product section
    """

    PRODUCT = "product"

    CHOICES = [(PRODUCT, "product")]


class AppExtensionType:
    """All available types where app's iframe can be mounted.

    OVERVIEW - app's iframe will be mounted on list view.
    DETAILS - app's iframe will be mounted on detail view
    """

    OVERVIEW = "overview"
    DETAILS = "details"

    CHOICES = [(OVERVIEW, "overview"), (DETAILS, "details")]


class AppExtensionTarget:
    """All available places where app's iframe can be mounted.

    MORE_ACTIONS - more actions button
    CREATE - create button
    """

    MORE_ACTIONS = "more_actions"
    CREATE = "create"

    CHOICES = [(MORE_ACTIONS, "more_actions"), (CREATE, "create")]
