class AttributeDescriptions:
    INPUT_TYPE = "The input type to use for entering attribute values in the dashboard."
    NAME = "Name of an attribute displayed in the interface."
    SLUG = "Internal representation of an attribute name."
    VALUES = "List of attribute's values."
    IS_VARIANT_ONLY = "Whether the attribute is for variants only"


class AttributeValueDescriptions:
    NAME = "Name of a value displayed in the interface."
    SLUG = "Internal representation of a value (unique per attribute)."
    TYPE = """Type of value (used only when `value` field is set)."""
    VALUE = """Special value other than a textual name. Possible types are:
    string (default), CSS color property, CSS gradient property, URL
    (e.g. link to an image)."""
