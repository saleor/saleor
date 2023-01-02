from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from ...channel import ChannelContext
from ...core.enums import ErrorPolicyEnum
from ....core.permissions import ProductPermissions
from .product_bulk_create import ProductBulkCreateInput, ProductBulkCreate, \
    ProductBulkResult
from ....warehouse.models import Warehouse
from ....product import models
from ...core.types import BulkProductError, NonNullList


class ProductBulkUpdateInput(ProductBulkCreateInput):
    id = graphene.ID(required=True, description="ID of a product to update.")


class ProductBulkUpdate(ProductBulkCreate):
    class Arguments:
        products = NonNullList(
            ProductBulkUpdateInput,
            required=True,
            description="Fields required to update a product.",
        )
        error_policy = ErrorPolicyEnum(
            required=False,
            default_value=ErrorPolicyEnum.REJECT_EVERYTHING.name,
            description="Policies of error handling.",
        )

    class Meta:
        description = "Updates products."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = BulkProductError
        error_type_field = "bulk_product_errors"
        support_meta_field = True
        support_private_meta_field = True


    @classmethod
    def clean_products(cls, info, products_data, channels, warehouses, errors):
        cleaned_inputs = []
        sku_list = []
        import ipdb
        ipdb.set_trace()
        for product in products_data:

            cleaned_input = cls.clean_product_input(
                info,
                product,
                channels,
                warehouses,
                sku_list,
                product["id"],
                errors,

            )
            cleaned_inputs.append(cleaned_input if cleaned_input else None)
        return cleaned_inputs

    @classmethod
    def update_products(cls, info, cleaned_inputs, errors):
        instances = []
        # bulk update products implementation
        return instances

    @classmethod
    def perform_mutation(cls, root, info, **data):
        errors = defaultdict(list)
        data.pop("error_policy")

        channels = models.Channel.objects.all()
        warehouses = Warehouse.objects.all()

        cleaned_inputs = cls.clean_products(
            info, data["products"], channels, warehouses, errors
        )

        products_instances = cls.update_products(info, cleaned_inputs, errors)

        if errors:
            raise ValidationError(errors)

        products = [
            ChannelContext(node=instance, channel_slug=None)
            for instance in products_instances
        ]

        cls.send_events(info, products, updated_variants, updated_channels)

        return ProductBulkUpdate(
            count=len(products),
            results=[ProductBulkResult(product=product) for product in products],
        )


