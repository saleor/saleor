from babel.numbers import get_currency_precision, is_currency

from django.core.validators import (
    DecimalValidator, MaxValueValidator, MinValueValidator, ValidationError)

from .templatetags.prices_i18n import format_price


class MoneyPrecisionValidator(DecimalValidator):
    def __init__(self, currency, *args):
        self.currency = currency
        super(MoneyPrecisionValidator, self).__init__(*args)

    def __call__(self, other):
        if self.currency != other.currency:
            raise ValueError('Invalid currency: %r (expected %r)' % (
                other.currency, self.currency))

        value = other.amount
        super(MoneyPrecisionValidator, self).__call__(value)

        if is_currency(self.currency):
            currency_precision = get_currency_precision(self.currency)
            exponent = value.as_tuple()[-1]
            if exponent >= 0:
                decimals = 0
            else:
                decimals = abs(exponent)
            if decimals > currency_precision:
                raise ValidationError(
                    self.messages['max_decimal_places'],
                    code='max_decimal_places',
                    params={'max': currency_precision})


class MoneyValueValidator:
    def __call__(self, value):
        cleaned = self.clean(value)
        if self.compare(cleaned, self.limit_value):
            currency = self.limit_value.currency
            params = {
                'limit_value': format_price(self.limit_value.amount, currency),
                'show_value': format_price(cleaned.amount, currency),
                'value': format_price(value.amount, currency)}
            raise ValidationError(self.message, code=self.code, params=params)


class MaxMoneyValidator(MoneyValueValidator, MaxValueValidator):
    pass


class MinMoneyValidator(MoneyValueValidator, MinValueValidator):
    pass
