from graphql import DEFAULT_DEPRECATION_REASON as DEFAULT_DEPRECATION_REASON

# Deprecation message for input fields and query arguments. Use it, when
# deprecation message needs to be included in the field description.
DEPRECATED_IN_3X_INPUT = "\n\nDEPRECATED: this field will be removed."

DEPRECATED_IN_3X_TYPE = "\n\nDEPRECATED: this type will be removed."

DEPRECATED_IN_3X_EVENT = "\n\nDEPRECATED: this event will be removed."

ADDED_IN_318 = "\n\nAdded in Saleor 3.18."
ADDED_IN_319 = "\n\nAdded in Saleor 3.19."
ADDED_IN_320 = "\n\nAdded in Saleor 3.20."
ADDED_IN_321 = "\n\nAdded in Saleor 3.21."


PREVIEW_FEATURE = (
    "\n\nNote: this API is currently in Feature Preview and can be subject to "
    "changes at later point."
)

CHANNEL_REQUIRED = (
    "\n\nThis option requires a channel filter to work as the values can vary "
    "between channels."
)

RICH_CONTENT = "\n\nRich text format. For reference see https://editorjs.io/"
