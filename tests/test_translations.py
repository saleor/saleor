import pytest

from saleor.product.models import ProductTranslation


@pytest.fixture
def product_translation_fr(db, product_in_stock):
    return ProductTranslation.objects.create(
        language_code='fr', product=product_in_stock, name='French name')


@pytest.fixture
def product_translation_pl(db, product_in_stock):
    return ProductTranslation.objects.create(
        language_code='pl', product=product_in_stock, name='Polish name')


def test_translation(product_in_stock, settings, product_translation_fr):
    assert product_in_stock.translated.name == 'Test product'

    settings.LANGUAGE_CODE = 'fr'
    assert product_in_stock.translated.name == 'French name'


def test_translation_str_returns_str_of_instance(
        product_in_stock, product_translation_fr, settings):
    assert str(product_in_stock.translated) == str(product_in_stock)
    settings.LANGUAGE_CODE = 'fr'
    assert str(
        product_in_stock.translated.translation) == str(product_translation_fr)


def test_wrapper_gets_proper_wrapper(product_in_stock, product_translation_fr,
                                     settings, product_translation_pl):
    assert product_in_stock.translated.translation is None

    settings.LANGUAGE_CODE = 'fr'
    assert product_in_stock.translated.translation == product_translation_fr

    settings.LANGUAGE_CODE = 'pl'
    assert product_in_stock.translated.translation == product_translation_pl


def test_getattr(
        product_in_stock, settings, product_translation_fr, product_class):
    settings.LANGUAGE_CODE = 'fr'
    assert product_in_stock.translated.product_class == product_class


def test_translation_not_override_id(
        settings, product_in_stock, product_translation_fr):
    settings.LANGUAGE_CODE = 'fr'
    translated_product = product_in_stock.translated
    assert translated_product.id == product_in_stock.id
    assert not translated_product.id == product_translation_fr
