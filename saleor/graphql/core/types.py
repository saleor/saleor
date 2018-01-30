import graphene
from django_prices.templatetags import prices_i18n


class PriceType(graphene.ObjectType):
    currency = graphene.String()
    gross = graphene.Float()
    gross_localized = graphene.String()
    net = graphene.Float()
    net_localized = graphene.String()

    def resolve_gross_localized(self, info):
        return prices_i18n.gross(self)

    def resolve_net_localized(self, info):
        return prices_i18n.net(self)


class PriceField(graphene.Field):
    def __init__(self, *args, **kwargs):
        super().__init__(lambda: PriceType, *args, **kwargs)


class PriceRangeType(graphene.ObjectType):
    max_price = PriceField()
    min_price = PriceField()


class PriceRangeField(graphene.Field):
    def __init__(self, *args, **kwargs):
        super().__init__(lambda: PriceRangeType, *args, **kwargs)
