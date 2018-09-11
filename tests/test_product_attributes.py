import pytest

from saleor.product.models import (
    AttributeChoiceValue, Product, ProductAttribute)
from saleor.product.utils.attributes import (
    generate_name_from_values, get_attributes_display_map,
    get_name_from_attributes)


@pytest.fixture()
def product_with_no_attributes(product_type, category):
    product = Product.objects.create(
        name='Test product', price='10.00', product_type=product_type,
        category=category)
    return product


def test_get_attributes_display_map(product):
    attributes = product.product_type.product_attributes.all()
    attributes_display_map = get_attributes_display_map(
        product, attributes)

    product_attr = product.product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    assert len(attributes_display_map) == 1
    assert {k: v.pk for k, v in attributes_display_map.items()} == {
        product_attr.pk: attr_value.translated.pk}


def test_get_attributes_display_map_empty(product_with_no_attributes):
    product = product_with_no_attributes
    attributes = product.product_type.product_attributes.all()
    assert get_attributes_display_map(product, attributes) == {}


def test_get_name_from_attributes(product):
    variant = product.variants.first()
    attributes = variant.product.product_type.variant_attributes.all()
    name = get_name_from_attributes(variant, attributes)
    assert name == 'Small'


def test_get_name_from_attributes_no_attributes(product_with_no_attributes):
    variant_without_attributes = product_with_no_attributes.variants.create(
        sku='example-sku')
    variant = variant_without_attributes
    attributes = variant.product.product_type.variant_attributes.all()
    name = get_name_from_attributes(variant, attributes)
    assert name == ''


def test_generate_name_from_values():
    attribute = ProductAttribute.objects.create(
        slug='color', name='Color')
    red = AttributeChoiceValue.objects.create(
        attribute=attribute, name='Red', slug='red')
    blue = AttributeChoiceValue.objects.create(
        attribute=attribute, name='Blue', slug='blue')
    yellow = AttributeChoiceValue.objects.create(
        attribute=attribute, name='Yellow', slug='yellow')
    values = {'3': red, '2': blue, '1': yellow}
    name = generate_name_from_values(values)
    assert name == 'Yellow / Blue / Red'


def test_generate_name_from_values_empty():
    name = generate_name_from_values({})
    assert name == ''
