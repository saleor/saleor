import pytest

from ....attribute import AttributeType
from ....attribute.models import Attribute
from ... import ProductTypeKind
from ...models import ProductType


@pytest.fixture
def product_type_generator(
    attribute_generator, attribute_value_generator, default_tax_class
):
    def create_product_type(
        name="Default Type",
        slug="default-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
        tax_class=default_tax_class,
        product_attributes=None,
        variant_attributes=None,
    ):
        product_type = ProductType.objects.create(
            name=name,
            slug=slug,
            kind=kind,
            has_variants=has_variants,
            is_shipping_required=is_shipping_required,
            tax_class=tax_class,
        )
        if product_attributes is None:
            product_attribute = attribute_generator(
                external_reference="colorAttributeExternalReference",
                slug="color",
                name="Color",
                type=AttributeType.PRODUCT_TYPE,
                filterable_in_storefront=True,
                filterable_in_dashboard=True,
                available_in_grid=True,
            )

            attribute_value_generator(
                external_reference="colorAttributeValue1ExternalReference",
                name="Red",
                slug="red",
                attribute=product_attribute,
            )

            product_attributes = [product_attribute]
        if variant_attributes is None:
            variant_attribute = attribute_generator(
                external_reference="sizeAttributeExternalReference",
                slug="size",
                name="Size",
                type=AttributeType.PRODUCT_TYPE,
                filterable_in_storefront=True,
                filterable_in_dashboard=True,
                available_in_grid=True,
            )

            attribute_value_generator(
                name="Small",
                slug="small",
                attribute=variant_attribute,
            )
            variant_attributes = [variant_attribute]

        product_type.product_attributes.add(*product_attributes)
        product_type.variant_attributes.add(
            *variant_attributes, through_defaults={"variant_selection": True}
        )
        return product_type

    return create_product_type


@pytest.fixture
def product_type(product_type_generator):
    return product_type_generator()


@pytest.fixture
def product_type_with_product_attributes(attribute_without_values):
    product_type = ProductType.objects.create(
        name="product_type_with_product_attributes",
        slug="product-type-with-product-attributes",
        has_variants=False,
        is_shipping_required=False,
        weight=0,
    )
    product_type.product_attributes.add(attribute_without_values)
    return product_type


@pytest.fixture
def product_type_with_variant_attributes(attribute_without_values):
    product_type = ProductType.objects.create(
        name="product_type_with_variant_attributes",
        slug="product-type-with-variant-attributes",
        has_variants=False,
        is_shipping_required=False,
        weight=0,
    )
    product_type.variant_attributes.add(attribute_without_values)
    return product_type


@pytest.fixture
def product_type_with_value_required_attributes(
    color_attribute, size_attribute, default_tax_class
):
    product_type = ProductType.objects.create(
        name="Default Type",
        slug="default-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
        tax_class=default_tax_class,
    )
    color_attribute.value_required = True
    size_attribute.value_required = True
    Attribute.objects.bulk_update([color_attribute, size_attribute], ["value_required"])
    product_type.product_attributes.add(color_attribute)
    product_type.product_attributes.add(size_attribute)
    return product_type


@pytest.fixture
def product_type_list():
    product_type_1 = ProductType.objects.create(
        name="Type 1", slug="type-1", kind=ProductTypeKind.NORMAL
    )
    product_type_2 = ProductType.objects.create(
        name="Type 2", slug="type-2", kind=ProductTypeKind.NORMAL
    )
    product_type_3 = ProductType.objects.create(
        name="Type 3", slug="type-3", kind=ProductTypeKind.NORMAL
    )
    return product_type_1, product_type_2, product_type_3


@pytest.fixture
def non_shippable_gift_card_product_type(db):
    product_type = ProductType.objects.create(
        name="Gift card type no shipping",
        slug="gift-card-type-no-shipping",
        kind=ProductTypeKind.GIFT_CARD,
        has_variants=True,
        is_shipping_required=False,
    )
    return product_type


@pytest.fixture
def shippable_gift_card_product_type(db):
    product_type = ProductType.objects.create(
        name="Gift card type with shipping",
        slug="gift-card-type-with-shipping",
        kind=ProductTypeKind.GIFT_CARD,
        has_variants=True,
        is_shipping_required=True,
    )
    return product_type


@pytest.fixture
def product_type_with_rich_text_attribute(rich_text_attribute):
    product_type = ProductType.objects.create(
        name="Default Type",
        slug="default-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(rich_text_attribute)
    product_type.variant_attributes.add(rich_text_attribute)
    return product_type


@pytest.fixture
def product_type_without_variant():
    product_type = ProductType.objects.create(
        name="Type",
        slug="type",
        has_variants=False,
        is_shipping_required=True,
        kind=ProductTypeKind.NORMAL,
    )
    return product_type
