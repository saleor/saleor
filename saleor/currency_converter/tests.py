from __future__ import unicode_literals

from decimal import Decimal

from mock import patch
from django.test import TestCase
from prices import Price

from .utils import convert_price
from .backends import BaseRateBackend
from .models import RateSource


class FakeBackend(BaseRateBackend):
    source_name = 'fake'
    base_currency = 'USD'

    def get_rates(self):
        pass

    def update_rates(self):
        pass


fake_rate_source = RateSource(name='fake', base_currency='USD')


@patch('saleor.currency_converter.utils.get_default_backend',
       return_value=FakeBackend())
@patch('saleor.currency_converter.utils.get_rate_source',
       return_value=fake_rate_source)
class CurrencyConverterTestCase(TestCase):
    def setUp(self):
        self.price = Price(10, currency='USD')
        self.target_currency = 'EUR'

    @patch('saleor.currency_converter.utils.get_rate', return_value=3)
    def test_convert_price_rate_as_int(self, *mocks):
        converted = convert_price(self.price, self.target_currency)
        self.assertTrue(converted.gross == self.price.gross * 3)

    @patch('saleor.currency_converter.utils.get_rate',
           return_value=Decimal(0.51))
    def test_convert_price_rate_as_decimal(self, *mocks):
        converted = convert_price(self.price, self.target_currency)
        expected_value = (self.price * Decimal(0.51)).quantize(Decimal('1.00'))
        self.assertEqual(converted.gross, expected_value.gross)

    @patch('saleor.currency_converter.utils.get_rate',
           return_value=Decimal(1))
    def test_convert_price_the_same_currencies(self, *mocks):
        converted = convert_price(self.price, self.price.currency)
        self.assertEqual(converted.gross, converted.gross)
        self.assertEqual(converted.currency, converted.currency)


    @patch('saleor.currency_converter.utils.get_rate',
           return_value=1)
    def test_new_price_has_correct_currency(self, get_rate_mock, *mocks):
        converted = convert_price(self.price, self.target_currency)
        self.assertEqual(converted.currency, self.target_currency)
        get_rate_mock.assert_called_with(self.target_currency)
