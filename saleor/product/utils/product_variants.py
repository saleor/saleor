from django.core.exceptions import ValidationError

from ..error_codes import ProductErrorCode


def product_variant_exist(product):
    if product.variants.first() is None:
        raise ValidationError(
            {
                "product": ValidationError(
                    f"Cannot manage product `{product.id}` without variant.",
                )
            }
        )


def products_variant_exist(products):
    errors = []
    for product in products:
        try:
            product_variant_exist(product)
        except ValidationError as exc:
            errors.append(exc.message_dict)

    if errors:
        raise ValidationError(errors, code=ProductErrorCode.PRODUCT_WITHOUT_VARIANT)
