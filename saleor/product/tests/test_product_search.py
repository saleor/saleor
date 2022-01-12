from ...attribute import AttributeInputType, AttributeType
from ...attribute.models import Attribute, AttributeValue
from ...attribute.utils import associate_attribute_values_to_instance
from ...core.utils.editorjs import clean_editor_js
from ..models import Product, ProductVariant
from ..search import (
    prepare_product_search_document_value,
    update_product_search_document,
    update_products_search_document,
)


def test_update_product_search_document(product_type, category):
    # given
    name = "Test product"
    description = "Test description"
    product = Product.objects.create(
        name=name,
        slug="test-product-111",
        product_type=product_type,
        category=category,
        description_plaintext=description,
    )
    assert not product.search_document

    # when
    update_product_search_document(product)

    # then
    assert f"{name}\n{description}\n".lower() in product.search_document


def test_update_products_search_document(product_list):
    # given
    for product in product_list:
        product.search_document = ""
    Product.objects.bulk_update(product_list, ["search_document"])

    # when
    update_products_search_document(Product.objects.all())

    # then
    for product in product_list:
        product.refresh_from_db()
        assert product.search_document


def test_prepare_product_search_document_value_empty_product(product_type, category):
    # given
    name = "Test product"
    description = "Test description"
    product = Product.objects.create(
        name=name,
        slug="test-product-11",
        product_type=product_type,
        category=category,
        description_plaintext=description,
    )

    # when
    search_document_value = prepare_product_search_document_value(product)

    # then
    assert search_document_value == f"{name}\n{description}\n".lower()


def test_prepare_product_search_document_value(
    category,
    product_type,
    rich_text_attribute_with_many_values,
    date_time_attribute,
    date_attribute,
    color_attribute,
    size_attribute,
    numeric_attribute,
):
    # given
    multiselect_attribute = Attribute.objects.create(
        slug="modes",
        name="Available Modes",
        input_type=AttributeInputType.MULTISELECT,
        type=AttributeType.PRODUCT_TYPE,
    )

    multiselect_attr_val_1 = AttributeValue.objects.create(
        attribute=multiselect_attribute, name="Eco Mode", slug="eco"
    )
    multiselect_attr_val_2 = AttributeValue.objects.create(
        attribute=multiselect_attribute, name="Performance Mode", slug="power"
    )

    name = "Test product"
    description = "Test description"
    product = Product.objects.create(
        name=name,
        slug="test-product-11",
        product_type=product_type,
        category=category,
        description_plaintext=description,
    )

    product_type.product_attributes.add(
        rich_text_attribute_with_many_values,
        date_time_attribute,
        color_attribute,
        numeric_attribute,
    )
    rich_text_val_1 = rich_text_attribute_with_many_values.values.first()
    date_time_value = date_time_attribute.values.first()
    color_attribute_value = color_attribute.values.first()
    numeric_attribute_value = numeric_attribute.values.first()
    associate_attribute_values_to_instance(
        product, rich_text_attribute_with_many_values, rich_text_val_1
    )
    associate_attribute_values_to_instance(
        product, date_time_attribute, date_time_value
    )
    associate_attribute_values_to_instance(
        product, color_attribute, color_attribute_value
    )
    associate_attribute_values_to_instance(
        product, numeric_attribute, numeric_attribute_value
    )

    variant = ProductVariant.objects.create(product=product, sku="123")
    product_type.variant_attributes.add(
        rich_text_attribute_with_many_values,
        date_attribute,
        size_attribute,
        multiselect_attribute,
    )
    rich_text_val_2 = rich_text_attribute_with_many_values.values.last()
    size_attribute_value = size_attribute.values.first()
    date_attribute_value = date_attribute.values.first()
    associate_attribute_values_to_instance(
        variant, rich_text_attribute_with_many_values, rich_text_val_2
    )
    associate_attribute_values_to_instance(
        variant, size_attribute, size_attribute_value
    )
    associate_attribute_values_to_instance(
        variant, date_attribute, date_attribute_value
    )

    variant_2 = ProductVariant.objects.create(product=product, sku="123ABC")
    associate_attribute_values_to_instance(
        variant_2, multiselect_attribute, multiselect_attr_val_1, multiselect_attr_val_2
    )

    # when
    search_document_value = prepare_product_search_document_value(product)

    # then
    assert f"{name}\n{description}\n".lower() in search_document_value
    assert variant.sku.lower() in search_document_value
    assert variant_2.sku.lower() in search_document_value

    # check if product attributes are in search_document_value
    assert (
        clean_editor_js(rich_text_val_1.rich_text, to_string=True).lower()
        in search_document_value
    )
    assert date_time_value.date_time.isoformat().lower() in search_document_value
    assert color_attribute_value.name.lower() in search_document_value
    assert (
        f"{numeric_attribute_value.name}{numeric_attribute.unit}"
        in search_document_value
    )

    # check if variant attributes are in search_document_value
    assert (
        clean_editor_js(rich_text_val_2.rich_text, to_string=True).lower()
        in search_document_value
    )
    assert size_attribute_value.name.lower() in search_document_value
    assert date_attribute_value.date_time.isoformat().lower() in search_document_value
    assert multiselect_attr_val_1.name.lower() in search_document_value
    assert multiselect_attr_val_2.name.lower() in search_document_value
