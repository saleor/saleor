import pytest

from ....tests.utils import dummy_editorjs
from ...models import AttributeTranslation, AttributeValueTranslation
from ...utils import associate_attribute_values_to_instance


@pytest.fixture
def translated_attribute(product):
    attribute = product.product_type.product_attributes.first()
    return AttributeTranslation.objects.create(
        language_code="fr", attribute=attribute, name="French attribute name"
    )


@pytest.fixture
def translated_attribute_value(pink_attribute_value):
    return AttributeValueTranslation.objects.create(
        language_code="fr",
        attribute_value=pink_attribute_value,
        name="French attribute value name",
    )


@pytest.fixture
def translated_page_unique_attribute_value(page, rich_text_attribute_page_type):
    page_type = page.page_type
    page_type.page_attributes.add(rich_text_attribute_page_type)
    attribute_value = rich_text_attribute_page_type.values.first()
    associate_attribute_values_to_instance(
        page, {rich_text_attribute_page_type.id: [attribute_value]}
    )
    return AttributeValueTranslation.objects.create(
        language_code="fr",
        attribute_value=attribute_value,
        rich_text=dummy_editorjs("French description."),
    )


@pytest.fixture
def translated_product_unique_attribute_value(product, rich_text_attribute):
    product_type = product.product_type
    product_type.product_attributes.add(rich_text_attribute)
    attribute_value = rich_text_attribute.values.first()
    associate_attribute_values_to_instance(
        product, {rich_text_attribute.id: [attribute_value]}
    )
    return AttributeValueTranslation.objects.create(
        language_code="fr",
        attribute_value=attribute_value,
        rich_text=dummy_editorjs("French description."),
    )


@pytest.fixture
def translated_variant_unique_attribute_value(variant, rich_text_attribute):
    product_type = variant.product.product_type
    product_type.variant_attributes.add(rich_text_attribute)
    attribute_value = rich_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant, {rich_text_attribute.id: [attribute_value]}
    )
    return AttributeValueTranslation.objects.create(
        language_code="fr",
        attribute_value=attribute_value,
        rich_text=dummy_editorjs("French description."),
    )
