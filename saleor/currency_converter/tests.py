from __future__ import unicode_literals

from decimal import Decimal
from mock import patch
from django.test import TestCase

from prices import Price
from .utils import convert_price


class CurrencyConverterTestCase(TestCase):
    def setUp(self):
        self.price = Price(10, currency='USD')
        self.target_currency = 'EUR'

    @patch('saleor.currency_converter.utils.get_rate', return_value=1)
    def test_new_price_has_correct_currency(self, get_rate_mock):
        converted = convert_price(self.price, self.target_currency)
        self.assertEqual(converted.currency, self.target_currency)
        get_rate_mock.assert_called_with(self.target_currency)

    @patch('saleor.currency_converter.utils.get_rate', return_value=3)
    def test_convert_price_rate_as_int(self, mock_test):
        converted = convert_price(self.price, self.target_currency)
        self.assertTrue(converted.gross == self.price.gross * 3)

    @patch('saleor.currency_converter.utils.get_rate',
           return_value=Decimal(0.51))
    def test_convert_price_rate_as_decimal(self, mock_test):
        converted = convert_price(self.price, self.target_currency)
        expected_value = (self.price * Decimal(0.51)).quantize(Decimal('1.00'))
        self.assertEqual(converted.gross, expected_value.gross)

    @patch('saleor.currency_converter.utils.get_rate',
           return_value=Decimal(1))
    def test_convert_price_the_same_currencies(self, mock_test):
        converted = convert_price(self.price, self.price.currency)
        self.assertEqual(converted.gross, converted.gross)
        self.assertEqual(converted.currency, converted.currency)