import graphene
from django_prices.templatetags import prices_i18n
from graphene_django import DjangoObjectType


class CountableConnection(graphene.relay.Connection):
    class Meta:
        abstract = True

    total_count = graphene.Int(
        description='A total count of items in the collection')

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return root.length


class CountableDjangoObjectType(DjangoObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        # Force it to use the countable connection
        countable_conn = CountableConnection.create_type(
            "{}CountableConnection".format(cls.__name__),
            node=cls)
        super().__init_subclass_with_meta__(
            *args, connection=countable_conn, **kwargs)


class Error(graphene.ObjectType):
    field = graphene.String(
        description='Name of a field that caused the error.')
    message = graphene.String(description='The error message.')

    class Meta:
        description = 'Represents an error in the input of a mutation.'


class Money(graphene.ObjectType):
    currency = graphene.String(description='Currency code.')
    amount = graphene.Float(description='Amount of money.')
    localized = graphene.String(
        description='Money formatted according to the current locale.')

    class Meta:
        description = 'Represents amount of money in specific currency.'

    def resolve_localized(self, info):
        return prices_i18n.amount(self)


class TaxedMoney(graphene.ObjectType):
    currency = graphene.String(description='Currency code.')
    gross = graphene.Field(
        Money, description='Amount of money including taxes.')
    net = graphene.Field(Money, description='Amount of money without taxes.')

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
