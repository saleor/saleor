import graphene
from django_prices.templatetags import prices_i18n

from ..enums import TaxRateType


class Money(graphene.ObjectType):
    currency = graphene.String(description='Currency code.', required=True)
    amount = graphene.Float(description='Amount of money.', required=True)
    localized = graphene.String(
        description='Money formatted according to the current locale.',
        required=True)

    class Meta:
        description = 'Represents amount of money in specific currency.'

    def resolve_localized(self, _info):
        return prices_i18n.amount(self)


class MoneyRange(graphene.ObjectType):
    start = graphene.Field(
        Money, description='Lower bound of a price range.')
    stop = graphene.Field(
        Money, description='Upper bound of a price range.')

    class Meta:
        description = 'Represents a range of amounts of money.'


class TaxedMoney(graphene.ObjectType):
    currency = graphene.String(description='Currency code.', required=True)
    gross = graphene.Field(
        Money, description='Amount of money including taxes.', required=True)
    net = graphene.Field(
        Money, description='Amount of money without taxes.', required=True)
    tax = graphene.Field(Money, description='Amount of taxes.', required=True)

    class Meta:
        description = """Represents a monetary value with taxes. In
        case when taxes were not applied, net and gross values will be equal.
        """


class TaxedMoneyRange(graphene.ObjectType):
    start = graphene.Field(
        TaxedMoney, description='Lower bound of a price range.')
    stop = graphene.Field(
        TaxedMoney, description='Upper bound of a price range.')

    class Meta:
        description = 'Represents a range of monetary values.'


class VAT(graphene.ObjectType):
    country_code = graphene.String(description='Country code.', required=True)
    standard_rate = graphene.Float(
        description='Standard VAT rate in percent.')
    reduced_rates = graphene.List(
        lambda: ReducedRate,
        description='Country\'s VAT rate exceptions for specific types of goods.',
        required=True)

    class Meta:
        description = 'Represents a VAT rate for a country.'

    def resolve_standard_rate(self, _info):
        return self.data.get('standard_rate')

    def resolve_reduced_rates(self, _info):
        reduced_rates = self.data.get('reduced_rates', {}) or {}
        return [
            ReducedRate(rate=rate, rate_type=rate_type)
            for rate_type, rate in reduced_rates.items()]


class ReducedRate(graphene.ObjectType):
    rate = graphene.Float(
        description='Reduced VAT rate in percent.', required=True)
    rate_type = TaxRateType(description='A type of goods.', required=True)

    class Meta:
        description = 'Represents a reduced VAT rate for a particular type of goods.'
