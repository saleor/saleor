import graphene
from django.db.models import Sum
from django.db.models.functions import Coalesce

from ...core.permissions import OrderPermissions, ProductPermissions
from ...warehouse import models
from ..account.enums import CountryCodeEnum
from ..channel import ChannelContext
from ..core.connection import CountableDjangoObjectType
from ..decorators import one_of_permissions_required


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
    slug = graphene.String(description="Warehouse slug.")
    company_name = graphene.String(description="Company name.")
    email = graphene.String(description="The email address of the warehouse.")


class WarehouseCreateInput(WarehouseInput):
    name = graphene.String(description="Warehouse name.", required=True)
    address = WarehouseAddressInput(
        description="Address of the warehouse.", required=True
    )
    shipping_zones = graphene.List(
        graphene.ID, description="Shipping zones supported by the warehouse."
    )


class WarehouseUpdateInput(WarehouseInput):
    name = graphene.String(description="Warehouse name.", required=False)
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
            "slug",
            "company_name",
            "shipping_zones",
            "address",
            "email",
        ]

    @staticmethod
    def resolve_shipping_zones(root, *_args, **_kwargs):
        instances = root.shipping_zones.all()
        shipping_zones = [
            ChannelContext(node=shipping_zone, channel_slug=None)
            for shipping_zone in instances
        ]
        return shipping_zones


class Stock(CountableDjangoObjectType):
    quantity = graphene.Int(
        required=True,
        description="Quantity of a product in the warehouse's possession, "
        "including the allocated stock that is waiting for shipment.",
    )
    quantity_allocated = graphene.Int(
        required=True, description="Quantity allocated for orders"
    )

    class Meta:
        description = "Represents stock."
        model = models.Stock
        interfaces = [graphene.relay.Node]
        only_fields = ["warehouse", "product_variant", "quantity", "quantity_allocated"]

    @staticmethod
    @one_of_permissions_required(
        [ProductPermissions.MANAGE_PRODUCTS, OrderPermissions.MANAGE_ORDERS]
    )
    def resolve_quantity(root, *_args):
        return root.quantity

    @staticmethod
    @one_of_permissions_required(
        [ProductPermissions.MANAGE_PRODUCTS, OrderPermissions.MANAGE_ORDERS]
    )
    def resolve_quantity_allocated(root, *_args):
        return root.allocations.aggregate(
            quantity_allocated=Coalesce(Sum("quantity_allocated"), 0)
        )["quantity_allocated"]

    @staticmethod
    def resolve_product_variant(root, *_args):
        return ChannelContext(node=root.product_variant, channel_slug=None)


class Allocation(CountableDjangoObjectType):
    quantity = graphene.Int(required=True, description="Quantity allocated for orders.")
    warehouse = graphene.Field(
        Warehouse, required=True, description="The warehouse were items were allocated."
    )

    class Meta:
        description = "Represents allocation."
        model = models.Allocation
        interfaces = [graphene.relay.Node]
        only_fields = ["id"]

    @staticmethod
    @one_of_permissions_required(
        [ProductPermissions.MANAGE_PRODUCTS, OrderPermissions.MANAGE_ORDERS]
    )
    def resolve_warehouse(root, *_args):
        return root.stock.warehouse

    @staticmethod
    @one_of_permissions_required(
        [ProductPermissions.MANAGE_PRODUCTS, OrderPermissions.MANAGE_ORDERS]
    )
    def resolve_quantity(root, *_args):
        return root.quantity_allocated
