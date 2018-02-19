import graphene
from django_prices.templatetags import prices_i18n
from graphene_django import DjangoObjectType


class CountableConnection(graphene.relay.Connection):
    class Meta:
        abstract = True

    total_count = graphene.Int()

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


class Price(graphene.ObjectType):
    currency = graphene.String()
    gross = graphene.Float()
    gross_localized = graphene.String()
    net = graphene.Float()
    net_localized = graphene.String()

    def resolve_gross_localized(self, info):
        return prices_i18n.gross(self)

    def resolve_net_localized(self, info):
        return prices_i18n.net(self)


class PriceRange(graphene.ObjectType):
    max_price = graphene.Field(Price)
    min_price = graphene.Field(Price)
