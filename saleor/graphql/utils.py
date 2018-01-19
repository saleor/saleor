import graphene
from django.shortcuts import _get_queryset
from django_prices.templatetags import prices_i18n


class CategoryAncestorsCache:
    """
    Cache used to store ancestors of a category in GraphQL context in order to
    reduce number of database queries. Categories of the same tree depth level
    have common ancestors, which allows us to cache them by the level.
    """

    def __init__(self, category):
        self._cache = {category.level: category.get_ancestors()}

    def get(self, category):
        if category.level not in self._cache:
            self._cache[category.level] = category.get_ancestors()
        return self._cache[category.level]


class DjangoPkInterface(graphene.Interface):
    """
    Exposes the Django model primary key
    """
    pk = graphene.ID(description="Primary key")

    def resolve_pk(self, info):
        return self.pk


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
