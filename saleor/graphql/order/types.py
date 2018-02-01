import graphene


class AddressInput(graphene.InputObjectType):
    address_line = graphene.List(graphene.String, required=True)
    city = graphene.String(required=True)
    country = graphene.String(required=True)
    dependent_locality = graphene.String()
    language_code = graphene.String()
    organization = graphene.String()
    phone = graphene.String()
    postal_code = graphene.String(required=True)
    recipient = graphene.String(required=True)
    region = graphene.String()
    sorting_code = graphene.String()


class DetailsInput(graphene.InputObjectType):
    billing_address = AddressInput()
    card_number = graphene.String(required=True)
    card_security_code = graphene.String(required=True)
    cardholder_name = graphene.String(required=True)
    expiry_month = graphene.String(required=True)
    expiry_year = graphene.String(required=True)
