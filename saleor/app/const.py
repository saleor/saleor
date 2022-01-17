from .types import (
    AppExtensionOpenAs,
    AppExtensionTarget,
    AppExtensionType,
    AppExtensionView,
)

# Stores all potential way of configuration of extension
AVAILABLE_APP_EXTENSION_CONFIGS = {
    AppExtensionType.DETAILS: {
        AppExtensionView.PRODUCT: [
            AppExtensionTarget.CREATE,
            AppExtensionTarget.MORE_ACTIONS,
        ]
    },
    AppExtensionType.OVERVIEW: {
        AppExtensionView.PRODUCT: [
            AppExtensionTarget.CREATE,
            AppExtensionTarget.MORE_ACTIONS,
        ]
    },
    AppExtensionType.NAVIGATION: {
        AppExtensionView.ALL: [
            AppExtensionTarget.CATALOG,
            AppExtensionTarget.ORDERS,
            AppExtensionTarget.CUSTOMERS,
            AppExtensionTarget.DISCOUNTS,
            AppExtensionTarget.TRANSLATIONS,
            AppExtensionTarget.PAGES,
        ]
    },
}

# Stores a values enum_type:field:is_optional for AppExtensions
EXTENSION_ENUM_MAP = [
    (AppExtensionView, "view", False),
    (AppExtensionType, "type", False),
    (AppExtensionTarget, "target", False),
    (AppExtensionOpenAs, "open_as", True),
]
# Stores a map of fields 'manifest-field:saleor-field
EXTENSION_FIELDS_MAP = [("openAs", "open_as")]
