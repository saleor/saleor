class AppType:
    LOCAL = "local"
    THIRDPARTY = "thirdparty"

    CHOICES = [(LOCAL, "local"), (THIRDPARTY, "thirdparty")]


# We need special handling for popup - if it declares relative extension URL, resolver will stitch if with app URL
POPUP_EXTENSION_TARGET = "popup"

# In case of not provided, use the default value as a fallback
DEFAULT_APP_TARGET = POPUP_EXTENSION_TARGET
