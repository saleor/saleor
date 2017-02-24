from mock import Mock

from saleor.product.models import ProductTranslation


def test_translation(monkeypatch, product_in_stock):

    product_in_stock.name = 'Foo'
    product_in_stock.save()

    ProductTranslation.objects.create(language_code='fr', product=product_in_stock, name='Bar')

    product_in_stock.refresh_from_db()

    assert product_in_stock.translated.name == 'Foo'

    monkeypatch.setattr('saleor.core.utils.get_language', Mock(return_value='fr'))

    assert product_in_stock.translated.name == 'Bar'
