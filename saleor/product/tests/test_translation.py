import pytest

from ...attribute.models import AttributeValueTranslation
from ...tests.utils import dummy_editorjs
from ..models import ProductTranslation, ProductVariantTranslation


@pytest.fixture
def product_translation_pl(product):
    return ProductTranslation.objects.create(
        language_code="pl",
        product=product,
        name="Polish name",
        description=dummy_editorjs("Polish description."),
    )


@pytest.fixture
def attribute_value_translation_fr(translated_attribute):
    value = translated_attribute.attribute.values.first()
    return AttributeValueTranslation.objects.create(
        language_code="fr", attribute_value=value, name="French name"
    )


def test_translation(product, settings, product_translation_fr):
    assert product.get_translation().name == "Test product"
    assert not product.get_translation().description

    settings.LANGUAGE_CODE = "fr"
    assert product.get_translation().name == "French name"
    assert product.get_translation().description == dummy_editorjs(
        "French description."
    )


def test_translation_str_returns_str_of_instance(
    product, product_translation_fr, settings
):
    assert str(product.get_translation()) == str(product)
    settings.LANGUAGE_CODE = "fr"
    assert str(product.get_translation().translation) == str(product_translation_fr)


def test_wrapper_gets_proper_wrapper(
    product, product_translation_fr, settings, product_translation_pl
):
    assert product.get_translation().translation is None

    settings.LANGUAGE_CODE = "fr"
    assert product.get_translation().translation == product_translation_fr

    settings.LANGUAGE_CODE = "pl"
    assert product.get_translation().translation == product_translation_pl


def test_getattr(product, settings, product_translation_fr, product_type):
    settings.LANGUAGE_CODE = "fr"
    assert product.get_translation().product_type == product_type


def test_translation_not_override_id(settings, product, product_translation_fr):
    settings.LANGUAGE_CODE = "fr"
    translated_product = product.get_translation()
    assert translated_product.id == product.id
    assert not translated_product.id == product_translation_fr


def test_product_variant_translation(settings, variant):
    settings.LANGUAGE_CODE = "fr"
    french_name = "French name"
    ProductVariantTranslation.objects.create(
        language_code="fr", name=french_name, product_variant=variant
    )
    assert variant.get_translation().name == french_name


def test_attribute_value_translation(settings, product, attribute_value_translation_fr):
    attribute = product.product_type.product_attributes.first().values.first()
    assert not attribute.get_translation().name == "French name"
    settings.LANGUAGE_CODE = "fr"
    assert attribute.get_translation().name == "French name"


def test_voucher_translation(settings, voucher, voucher_translation_fr):
    assert not voucher.get_translation().name == "French name"
    settings.LANGUAGE_CODE = "fr"
    assert voucher.get_translation().name == "French name"
