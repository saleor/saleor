class AppType:
    LOCAL = "local"
    THIRDPARTY = "thirdparty"

    CHOICES = [(LOCAL, "local"), (THIRDPARTY, "thirdparty")]


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
