class MediaOwnerTypes:
    """Entity kinds that can own media.

    Each value is both the name of the owner foreign key on the matching
    `BaseMedia` subclass and the value stored in webhook owner-type filters.
    """

    PRODUCT = "product"
    CATEGORY = "category"
    COLLECTION = "collection"
    PAGE = "page"

    CHOICES = [
        (PRODUCT, "A product."),
        (CATEGORY, "A category."),
        (COLLECTION, "A collection."),
        (PAGE, "A page."),
    ]

    ALL = [choice[0] for choice in CHOICES]


ALT_CHAR_LIMIT = 250
