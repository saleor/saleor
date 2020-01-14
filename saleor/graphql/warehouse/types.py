import graphene

from ...warehouse import models
from ..account.enums import CountryCodeEnum
from ..core.connection import CountableDjangoObjectType


class WarehouseAddressInput(graphene.InputObjectType):
    street_address_1 = graphene.String(description="Address.", required=True)
    street_address_2 = graphene.String(description="Address.")
    city = graphene.String(description="City.", required=True)
    city_area = graphene.String(description="District.")
    postal_code = graphene.String(description="Postal code.")
    country = CountryCodeEnum(description="Country.", required=True)
    country_area = graphene.String(description="State or province.")
    phone = graphene.String(description="Phone number.")


class WarehouseInput(graphene.InputObjectType):
    name = graphene.String(description="Warehouse name.", required=True)
    company_name = graphene.String(description="Company name.")
    shipping_zones = graphene.List(
        graphene.ID, description="Shipping zones supported by the warehouse."
    )
    email = graphene.String(description="The email address of the warehouse.")


class WarehouseCreateInput(WarehouseInput):
    address = WarehouseAddressInput(
        description="Address of the warehouse.", required=True
    )


class WarehouseUpdateInput(WarehouseInput):
    address = WarehouseAddressInput(
        description="Address of the warehouse.", required=False
    )


class Warehouse(CountableDjangoObjectType):
    class Meta:
        description = "Represents warehouse."
        model = models.Warehouse
        interfaces = [graphene.relay.Node]
        only_fields = [
            "id",
            "name",
            "company_name",
            "shipping_zones",
            "address",
            "email",
        ]
