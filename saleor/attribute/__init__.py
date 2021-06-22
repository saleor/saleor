default_app_config = "saleor.attribute.app.AttributeAppConfig"


class AttributeInputType:
    """The type that we expect to render the attribute's values as."""

    DROPDOWN = "dropdown"
    MULTISELECT = "multiselect"
    FILE = "file"
    REFERENCE = "reference"
    NUMERIC = "numeric"
    RICH_TEXT = "rich-text"
    BOOLEAN = "boolean"

    CHOICES = [
        (DROPDOWN, "Dropdown"),
        (MULTISELECT, "Multi Select"),
        (FILE, "File"),
        (REFERENCE, "Reference"),
        (NUMERIC, "Numeric"),
        (RICH_TEXT, "Rich Text"),
        (BOOLEAN, "Boolean"),
    ]

    # list of the input types that can be used in variant selection
    ALLOWED_IN_VARIANT_SELECTION = [DROPDOWN, BOOLEAN]

    TYPES_WITH_CHOICES = [
        DROPDOWN,
        MULTISELECT,
    ]

    # list of the input types that are unique per instances
    TYPES_WITH_UNIQUE_VALUES = [
        FILE,
        REFERENCE,
        RICH_TEXT,
        NUMERIC,
    ]


# list of input types that are allowed for given attribute property
ATTRIBUTE_PROPERTIES_CONFIGURATION = {
    "filterable_in_storefront": [
        AttributeInputType.DROPDOWN,
        AttributeInputType.MULTISELECT,
        AttributeInputType.NUMERIC,
        AttributeInputType.BOOLEAN,
    ],
    "filterable_in_dashboard": [
        AttributeInputType.DROPDOWN,
        AttributeInputType.MULTISELECT,
        AttributeInputType.NUMERIC,
        AttributeInputType.BOOLEAN,
    ],
    "available_in_grid": [
        AttributeInputType.DROPDOWN,
        AttributeInputType.MULTISELECT,
        AttributeInputType.NUMERIC,
        AttributeInputType.BOOLEAN,
    ],
    "storefront_search_position": [
        AttributeInputType.DROPDOWN,
        AttributeInputType.MULTISELECT,
        AttributeInputType.BOOLEAN,
    ],
}


class AttributeType:
    PRODUCT_TYPE = "product-type"
    PAGE_TYPE = "page-type"

    CHOICES = [(PRODUCT_TYPE, "Product type"), (PAGE_TYPE, "Page type")]


class AttributeEntityType:
    """Type of a reference entity type. Must match the name of the graphql type.

    After adding new value, `REFERENCE_VALUE_NAME_MAPPING`
    and `ENTITY_TYPE_TO_MODEL_MAPPING` in saleor/graphql/attribute/utils.py
    must be updated.
    """

    PAGE = "Page"
    PRODUCT = "Product"

    CHOICES = [(PAGE, "Page"), (PRODUCT, "Product")]
