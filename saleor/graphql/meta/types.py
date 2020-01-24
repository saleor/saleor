from operator import itemgetter

import graphene

from ...account import models as account_models
from ...checkout import models as checkout_models
from ...order import models as order_models
from ...product import models as product_models


class MetaPath(graphene.InputObjectType):
    namespace = graphene.String(
        required=True, description="Name of metadata client group."
    )
    client_name = graphene.String(required=True, description="Metadata client's name.")
    key = graphene.String(required=True, description="Key for stored data.")


class MetaInput(MetaPath):
    value = graphene.String(required=True, description="Stored metadata value.")


class MetaItem(graphene.ObjectType):
    key = graphene.String(required=True, description="Key for stored data.")
    value = graphene.String(required=True, description="Stored metadata value.")


class MetaClientStore(graphene.ObjectType):
    name = graphene.String(required=True, description="Metadata client's name.")
    metadata = graphene.List(
        MetaItem, required=True, description="Metadata stored for a client."
    )

    @staticmethod
    def resolve_metadata(root, _info):
        return sorted(
            [{"key": k, "value": v} for k, v in root["metadata"].items()],
            key=itemgetter("key"),
        )


class MetaStore(graphene.ObjectType):
    namespace = graphene.String(
        required=True, description="Name of metadata client group."
    )
    clients = graphene.List(
        MetaClientStore,
        required=True,
        description="List of clients that stored metadata in a group.",
    )

    @staticmethod
    def resolve_clients(root: dict, _info):
        return sorted(
            [
                {"name": key, "metadata": value}
                for key, value in root["metadata"].items()
            ],
            key=itemgetter("name"),
        )


class ObjectWithMetadata(graphene.Interface):
    private_meta = graphene.List(
        MetaStore,
        required=True,
        description="List of privately stored metadata namespaces.",
    )
    meta = graphene.List(
        MetaStore,
        required=True,
        description="List of publicly stored metadata namespaces.",
    )

    @classmethod
    def resolve_type(cls, instance, info):
        # Imports inside resolvers to avoid circular imports.
        from ..account import types as account_types
        from ..checkout import types as checkout_types
        from ..order import types as order_types
        from ..product import types as product_types

        if isinstance(instance, product_models.Attribute):
            return product_types.Attribute
        if isinstance(instance, product_models.Category):
            return product_types.Category
        if isinstance(instance, checkout_models.Checkout):
            return checkout_types.Checkout
        if isinstance(instance, product_models.Collection):
            return product_types.Collection
        if isinstance(instance, product_models.DigitalContent):
            return product_types.DigitalContent
        if isinstance(instance, order_models.Fulfillment):
            return order_types.Fulfillment
        if isinstance(instance, order_models.Order):
            return order_types.Order
        if isinstance(instance, product_models.Product):
            return product_types.Product
        if isinstance(instance, product_models.ProductType):
            return product_types.ProductType
        if isinstance(instance, product_models.ProductVariant):
            return product_types.ProductVariant
        if isinstance(instance, account_models.ServiceAccount):
            return account_types.ServiceAccount
        if isinstance(instance, account_models.User):
            return account_types.User
        return None
