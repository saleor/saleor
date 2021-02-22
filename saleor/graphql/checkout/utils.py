import graphene
from django.core.exceptions import ValidationError


def prepare_insufficient_stock_checkout_validation_error(exc):
    variants = [str(item.variant) for item in exc.items]
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", item.variant.pk)
        for item in exc.items
    ]
    return ValidationError(
        f"Insufficient product stock: {', '.join(variants)}",
        code=exc.code.value,
        params={"variants": variant_ids},
    )
