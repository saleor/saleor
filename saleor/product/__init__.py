MEDIA_URL_CHAR_LIMIT = 2048


class ProductMediaTypes:
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"

    CHOICES = [
        (IMAGE, "An uploaded image or an URL to an image"),
        (VIDEO, "A URL to an external video"),
    ]


class MediaOwnerTypes:
    """Entity types a `ProductMedia` row can be attached to.

    Values match the name of the owner foreign key on `ProductMedia`.
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


class ProductTypeKind:
    NORMAL = "normal"
    GIFT_CARD = "gift_card"

    CHOICES = [
        (NORMAL, "A standard product type."),
        (GIFT_CARD, "A gift card product type."),
    ]
