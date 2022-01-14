import graphene


class CountryFilterInput(graphene.InputObjectType):
    in_shipping_zones = graphene.Boolean()
