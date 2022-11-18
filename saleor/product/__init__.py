default_app_config = "saleor.product.app.ProductAppConfig"


class ProductMediaTypes:
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"

    CHOICES = [
        (IMAGE, "An uploaded image or an URL to an image"),
        (VIDEO, "A URL to an external video"),
    ]


class ProductTypeKind:
    NORMAL = "normal"
    GIFT_CARD = "gift_card"

    CHOICES = [
        (NORMAL, "A standard product type."),
        (GIFT_CARD, "A gift card product type."),
    ]


class CollectionType:
    STATIC = "static"
    DYNAMIC = "dynamic"

    CHOICES = [
        (STATIC, "Static"),
        (DYNAMIC, "Dynamic"),
    ]


class RuleOperator:
    IS = "is"
    IS_NOT = "is_not"

    CHOICES = [(IS, "Is"), (IS_NOT, "Is not")]


class RuleQualifier:
    ATTRIBUTE = "attribute"

    CHOICES = [(ATTRIBUTE, "Attribute")]
