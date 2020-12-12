class ShippingMethodType:
    PRICE_BASED = "price"
    WEIGHT_BASED = "weight"

    CHOICES = [
        (PRICE_BASED, "Price based shipping"),
        (WEIGHT_BASED, "Weight based shipping"),
    ]


class ZipCodeRuleInclusionType:
    INCLUDE = "include"
    EXCLUDE = "exclude"

    CHOICES = [
        (INCLUDE, "Shipping method should include ZIP code rule"),
        (EXCLUDE, "Shipping method should exclude ZIP code rule"),
    ]
