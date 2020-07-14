from collections import defaultdict
from typing import Iterable, List, Optional

from ..celeryconf import app
from ..discount.models import Sale
from .models import (
    AssignedVariantAttribute,
    Attribute,
    AttributeValue,
    AttributeVariant,
    Product,
    ProductType,
    ProductVariant,
)
from .utils.attributes import generate_name_for_variant
from .utils.variant_prices import (
    update_product_minimal_variant_price,
    update_products_minimal_variant_prices,
    update_products_minimal_variant_prices_of_catalogues,
    update_products_minimal_variant_prices_of_discount,
)


def _update_variants_names(instance: ProductType, saved_attributes: Iterable):
    """Product variant names are created from names of assigned attributes.

    After change in attribute value name, for all product variants using this
    attributes we need to update the names.
    """
    initial_attributes = set(instance.variant_attributes.all())
    attributes_changed = initial_attributes.intersection(saved_attributes)
    if not attributes_changed:
        return
    variants_to_be_updated = ProductVariant.objects.filter(
        product__in=instance.products.all(),
        product__product_type__variant_attributes__in=attributes_changed,
    )
    variants_to_be_updated = variants_to_be_updated.prefetch_related(
        "attributes__values__translations"
    ).all()
    for variant in variants_to_be_updated:
        variant.name = generate_name_for_variant(variant)
        variant.save(update_fields=["name"])


@app.task
def update_variants_names(product_type_pk: int, saved_attributes_ids: List[int]):
    instance = ProductType.objects.get(pk=product_type_pk)
    saved_attributes = Attribute.objects.filter(pk__in=saved_attributes_ids)
    _update_variants_names(instance, saved_attributes)


@app.task
def update_product_minimal_variant_price_task(product_pk: int):
    product = Product.objects.get(pk=product_pk)
    update_product_minimal_variant_price(product)


@app.task
def update_products_minimal_variant_prices_of_catalogues_task(
    product_ids: Optional[List[int]] = None,
    category_ids: Optional[List[int]] = None,
    collection_ids: Optional[List[int]] = None,
):
    update_products_minimal_variant_prices_of_catalogues(
        product_ids, category_ids, collection_ids
    )


@app.task
def update_products_minimal_variant_prices_of_discount_task(discount_pk: int):
    discount = Sale.objects.get(pk=discount_pk)
    update_products_minimal_variant_prices_of_discount(discount)


@app.task
def update_products_minimal_variant_prices_task(product_ids: List[int]):
    products = Product.objects.filter(pk__in=product_ids)
    update_products_minimal_variant_prices(products)


@app.task
def update_productvariant_sorting(
    attributevalue: Optional["AttributeValue"] = None,
    attributevariant: Optional["AttributeVariant"] = None,
    product: Optional["Product"] = None,
    productvariant: Optional["ProductVariant"] = None,
    product_type: Optional["ProductType"] = None,
    attribute: Optional["Attribute"] = None,
):
    def recalculate_sorting(product_ids: List[int]):
        product_ids = set(product_ids)
        for product in product_ids:
            variants_list = list(
                ProductVariant.objects.filter(product_id=product).values(
                    "id",
                    "name",
                    "attributes__assignment__attribute__name",
                    "attributes__values__name",
                    "attributes__assignment__sort_order",
                    "attributes__values__sort_order",
                )
            )

            all_variants = defaultdict(lambda: defaultdict(list))
            sort_keys = list()
            for x in variants_list:
                sort_keys.append(x["attributes__assignment__sort_order"])
                if x["attributes__values__sort_order"] is not None:
                    all_variants[x["id"]][
                        x["attributes__assignment__sort_order"]
                    ].append(x["attributes__values__sort_order"])

            sorted_variants = sorted(
                all_variants.items(),
                key=lambda x: (
                    [
                        x[1].get(i, [0]) if x[1].get(i, [0]) is not [None] else []
                        for i in sort_keys
                    ],
                ),
            )
            for sort_order, p in enumerate(sorted_variants):
                ProductVariant.objects.filter(pk=p[0]).update(
                    sort_by_attributes=sort_order
                )

    if product is not None:
        recalculate_sorting([product.pk])

    if productvariant is not None:
        recalculate_sorting([productvariant.product_id])

    if attributevariant is not None:
        products = attributevariant.assigned_variants.all().values_list(
            "product_id", flat=True
        )
        recalculate_sorting(products)

    if attributevalue is not None:
        products = AssignedVariantAttribute.objects.filter(
            values__in=[attributevalue]
        ).values_list("assignment", flat=True)
        recalculate_sorting(products)

    if product_type is not None:
        products = Product.objects.filter(product_type=product_type).values_list(
            "pk", flat=True
        )
        recalculate_sorting(products)

    if attribute is not None:
        products = Product.objects.filter(
            variants__attributes__attribute__in=[attribute]
        ).values_list("pk", flat=True)
        recalculate_sorting(products)
