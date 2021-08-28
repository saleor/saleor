import graphene
from django.core.exceptions import ValidationError

from ..core.types.common import MetadataError
from ..warehouse.types import Stock
from ...core.permissions import AccountPermissions
from ...graphql.core.mutations import ModelMutation
from ...graphql.stock_transfer import types
from ...stock_transfer import models


class StockTransferCreate(ModelMutation):
    class Arguments:
        input = types.StockTransferInput(
            required=True,
            description="Fields required to create a stock transfer request.",
        )

    class Meta:
        model = models.StockTransfer
        error_type_class = MetadataError
        description = "Create stock transfer request"
        error_type_field = "stock_transfer_errors"


class ApproveStockTransferRequest(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of a stock transfer to update.", required=True)
        input = types.UpdateStockTransferInput(
            required=True, description="Fields required to update stock transfer."
        )

    class Meta:
        model = models.StockTransfer
        error_type_class = MetadataError
        description = "Create stock transfer request"
        error_type_field = "stock_transfer_errors"
        permissions = (AccountPermissions.MANAGE_USERS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):

        try:
            stock_transfer = cls.get_node_or_error(info, data.get("id"),
                                                   only_type=types.StockTransfer)

            stock_start = cls.get_node_or_error(info, stock_transfer.stock_start,
                                                only_type=Stock)

            quantity_start = stock_start.quantity
            stock_start.quantity = stock_start.quantity - quantity_start
            stock_start.save()

            stock_target = cls.get_node_or_error(info, stock_transfer.stock_target,
                                                 only_type=Stock)
            stock_target.quantity = stock_target.quantity + quantity_start
            stock_target.save()
        except ValidationError as error:
            raise ValidationError({"error": error})

        return cls(**{cls._meta.return_field_name: stock_transfer})
