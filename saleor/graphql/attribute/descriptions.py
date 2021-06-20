class AttributeDescriptions:
    INPUT_TYPE = "The input type to use for entering attribute values in the dashboard."
    ENTITY_TYPE = "The entity type which can be used as a reference."
    NAME = "Name of an attribute displayed in the interface."
    SLUG = "Internal representation of an attribute name."
    TYPE = "The attribute type."
    UNIT = "The unit of attribute values."
    BOOLEAN = "The boolean value of the attribute."
    VALUES = "List of attribute's values."
    VALUE_REQUIRED = "Whether the attribute requires values to be passed or not."
    IS_VARIANT_ONLY = "Whether the attribute is for variants only."
    VISIBLE_IN_STOREFRONT = (
        "Whether the attribute should be visible or not in storefront."
    )
    FILTERABLE_IN_STOREFRONT = "Whether the attribute can be filtered in storefront."
    FILTERABLE_IN_DASHBOARD = "Whether the attribute can be filtered in dashboard."
    STOREFRONT_SEARCH_POSITION = (
        "The position of the attribute in the storefront navigation (0 by default)."
    )
    AVAILABLE_IN_GRID = (
        "Whether the attribute can be displayed in the admin product list."
    )


class AttributeValueDescriptions:
    ID = "The ID of a value displayed in the interface."
    NAME = "Name of a value displayed in the interface."
    SLUG = "Internal representation of a value (unique per attribute)."
    TYPE = "Type of value (used only when `value` field is set)."
    FILE = "Represents file URL and content type (if attribute value is a file)."
    VALUES_RANGE = "The range that the returned values should be in."
    VALUE = "Represents the value of the attribute value."
    RICH_TEXT = "Represents the text (JSON) of the attribute value."
    BOOLEAN = "Represents the boolean value of the attribute value."
    DATE = "Represents the date value of the attribute value."
    DATE_TIME = "Represents the date time value of the attribute value."
