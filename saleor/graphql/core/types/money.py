import graphene
from babel.numbers import get_currency_precision

from ....core.prices import quantize_price
from ...core.doc_category import DOC_CATEGORY_TAXES
from ...core.types import BaseObjectType


class Money(graphene.ObjectType):
    currency = graphene.String(description="Currency code.", required=True)
    amount = graphene.Float(description="Amount of money.", required=True)
    fractional_amount = graphene.Int(
        description="Amount of money represented as an integer in the smallest currency unit.",
        required=True,
    )
    fraction_digits = graphene.Int(
        description="Number of digits after the decimal point in the currency.",
        required=True,
    )

    class Meta:
        description = "Represents amount of money in specific currency."

    @staticmethod
    def resolve_amount(root, _info):
        return quantize_price(root.amount, root.currency)

    @staticmethod
    def resolve_fractional_amount(root, _info):
        precision = get_currency_precision(root.currency)
        return int(quantize_price(root.amount, root.currency) * (10**precision))

    @staticmethod
    def resolve_fraction_digits(root, _info):
        return get_currency_precision(root.currency)


class MoneyRange(graphene.ObjectType):
    start = graphene.Field(Money, description="Lower bound of a price range.")
    stop = graphene.Field(Money, description="Upper bound of a price range.")

    class Meta:
        description = "Represents a range of amounts of money."


class TaxedMoney(graphene.ObjectType):
    currency = graphene.String(description="Currency code.", required=True)
    gross = graphene.Field(
        Money, description="Amount of money including taxes.", required=True
    )
    net = graphene.Field(
        Money, description="Amount of money without taxes.", required=True
    )
    tax = graphene.Field(Money, description="Amount of taxes.", required=True)

    class Meta:
        description = (
            "Represents a monetary value with taxes. In cases where taxes were not "
            "applied, net and gross values will be equal."
        )


class TaxedMoneyRange(graphene.ObjectType):
    start = graphene.Field(TaxedMoney, description="Lower bound of a price range.")
    stop = graphene.Field(TaxedMoney, description="Upper bound of a price range.")

    class Meta:
        description = "Represents a range of monetary values."


class VAT(BaseObjectType):
    country_code = graphene.String(description="Country code.", required=True)
    standard_rate = graphene.Float(description="Standard VAT rate in percent.")
    reduced_rates = graphene.List(
        graphene.NonNull(lambda: ReducedRate),
        description="Country's VAT rate exceptions for specific types of goods.",
        required=True,
    )

    class Meta:
        description = "Represents a VAT rate for a country."
        doc_category = DOC_CATEGORY_TAXES

    @staticmethod
    def resolve_standard_rate(root, _info):
        return root.data.get("standard_rate")

    @staticmethod
    def resolve_reduced_rates(root, _info):
        reduced_rates = root.data.get("reduced_rates", {}) or {}
        return [
            ReducedRate(rate=rate, rate_type=rate_type)
            for rate_type, rate in reduced_rates.items()
        ]


class ReducedRate(BaseObjectType):
    rate = graphene.Float(description="Reduced VAT rate in percent.", required=True)
    rate_type = graphene.String(description="A type of goods.", required=True)

    class Meta:
        description = "Represents a reduced VAT rate for a particular type of goods."
        doc_category = DOC_CATEGORY_TAXES
