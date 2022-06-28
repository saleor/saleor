import graphene
from django.db import transaction

from ....core.permissions import DiscountPermissions
from ....core.tracing import traced_atomic_transaction
from ....discount import models
from ....discount.utils import fetch_catalogue_info
from ...core.mutations import ModelMutation
from ...core.types import DiscountError
from ..types import Sale
from .sale_create import SaleInput, SaleUpdateDiscountedPriceMixin
from .utils import convert_catalogue_info_to_global_ids


class SaleUpdate(SaleUpdateDiscountedPriceMixin, ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to update.")
        input = SaleInput(
            required=True, description="Fields required to update a sale."
        )

    class Meta:
        description = "Updates a sale."
        model = models.Sale
        object_type = Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")
        instance = cls.get_node_or_error(info, node_id, only_type=Sale)
        previous_catalogue = fetch_catalogue_info(instance)
        response = super().perform_mutation(_root, info, **data)
        current_catalogue = fetch_catalogue_info(instance)
        transaction.on_commit(
            lambda: info.context.plugins.sale_updated(
                instance,
                convert_catalogue_info_to_global_ids(previous_catalogue),
                convert_catalogue_info_to_global_ids(current_catalogue),
            )
        )
        return response
