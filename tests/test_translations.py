import pytest

from saleor.product.models import ProductTranslation


@pytest.fixture
def product_translation(db, product_in_stock):
    return ProductTranslation.objects.create(
        language_code='fr', product=product_in_stock, name='French name')


def test_translation(product_in_stock, settings, product_translation):
    assert product_in_stock.translated.name == 'Test product'

    settings.LANGUAGE_CODE = 'fr'
    assert product_in_stock.translated.name == 'French name'


def test_translation_str_returns_str_of_instance(
        product_in_stock, product_translation, settings):
    assert str(product_in_stock.translated) == str(product_in_stock)
    settings.LANGUAGE_CODE = 'fr'
    assert str(
        product_in_stock.translated.translation) == str(product_translation)
