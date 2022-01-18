import graphene


class CountryFilterInput(graphene.InputObjectType):
    attached_to_shipping_zones = graphene.Boolean(
        description="Boolean for filtering countries by having shipping zone assigned."
        "If 'true', return countries with shipping zone assigned."
        "If 'false', return countries without any shipping zone assigned."
        "If the argument is not provided (null), return all countries."
    )
