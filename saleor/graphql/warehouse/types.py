import graphene

from ...core.permissions import StockPermissions
from ...warehouse import models
from ...warehouse.availability import get_available_quantity_for_customer
from ..account.enums import CountryCodeEnum
from ..core.connection import CountableDjangoObjectType
from ..decorators import permission_required


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


class StockInput(graphene.InputObjectType):
    product_variant = graphene.ID(
        required=True, description="Product variant associated with stock."
    )
    warehouse = graphene.ID(
        required=True, description="Warehouse in which stock is located."
    )
    quantity = graphene.Int(description="Quantity of items available for sell.")


class Stock(CountableDjangoObjectType):
    available = graphene.Int(description="Quantity of a product available for sale.")

    class Meta:
        description = "Represents stock."
        model = models.Stock
        interfaces = [graphene.relay.Node]
        only_fields = ["warehouse", "product_variant", "quantity", "quantity_allocated"]

    @staticmethod
    @permission_required(StockPermissions.MANAGE_STOCKS)
    def resolve_available(root, *_args):
        return get_available_quantity_for_customer(root)
