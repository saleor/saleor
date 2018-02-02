from django_prices.templatetags import prices_i18n
import graphene


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


class PriceRangeType(graphene.ObjectType):
    max_price = graphene.Field(lambda: PriceType)
    min_price = graphene.Field(lambda: PriceType)
