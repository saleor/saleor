class AttributeInputType:
    """The type that we expect to render the attribute's values as."""

    DROPDOWN = "dropdown"
    MULTISELECT = "multiselect"

    CHOICES = [
        (DROPDOWN, "Dropdown"),
        (MULTISELECT, "Multi Select"),
    ]
    # list the input types that cannot be assigned to a variant
    NON_ASSIGNABLE_TO_VARIANTS = [MULTISELECT]


class AttributeType:
    PRODUCT_TYPE = "product-type"
    PAGE_TYPE = "page-type"

    CHOICES = [(PRODUCT_TYPE, "Product type"), (PAGE_TYPE, "Page type")]
