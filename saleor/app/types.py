class AppType:
    LOCAL = "local"
    THIRDPARTY = "thirdparty"

    CHOICES = [(LOCAL, "local"), (THIRDPARTY, "thirdparty")]


class AppExtensionView:
    PRODUCT = "product"

    CHOICES = [(PRODUCT, "product")]


class AppExtensionType:
    OVERVIEW = "overview"
    DETAILS = "details"

    CHOICES = [(OVERVIEW, "overview"), (DETAILS, "details")]


class AppExtensionMountingPlace:
    MORE_ACTIONS = "more_actions"
    CREATE = "create"

    CHOICES = [(MORE_ACTIONS, "more_actions"), (CREATE, "create")]
