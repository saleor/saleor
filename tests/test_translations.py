from mock import Mock

from saleor.product.models import ProductTranslation


def test_translation(product_in_stock, settings):
    ProductTranslation.objects.create(
        language_code='fr', product=product_in_stock, name='French name')
    assert product_in_stock.translated.name == 'Test product'

    settings.LANGUAGE_CODE = 'fr'
    assert product_in_stock.translated.name == 'French name'
