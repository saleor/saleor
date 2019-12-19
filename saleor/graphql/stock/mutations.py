import graphene

from ...stock import models
from ..core.mutations import ModelBulkDeleteMutation, ModelDeleteMutation, ModelMutation
from ..core.types.common import StockError
from .types import StockInput


class StockCreate(ModelMutation):
    class Arguments:
        input = StockInput(
            required=True, description="Fields required to create stock."
        )

    class Meta:
        description = "Creates new stock."
        model = models.Stock
        permissions = ("stock.manage_stocks",)
        error_type_class = StockError
        error_type_field = "stock_errors"


class StockUpdate(ModelMutation):
    class Arguments:
        input = StockInput(
            required=True, description="Fields required to update stock."
        )
        id = graphene.ID(required=True, description="ID of stock to update.")

    class Meta:
        model = models.Stock
        permissions = ("stock.manage_stocks",)
        description = "Update given stock."
        error_type_class = StockError
        error_type_field = "stock_error"


class StockDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of stock to delete.")

    class Meta:
        model = models.Stock
        permissions = ("stock.manage_stocks",)
        description = "Deletes selected stock."
        erorr_type_class = StockError
        error_type_field = "stock_error"


class StockBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(graphene.ID, required=True)

    class Meta:
        model = models.Stock
        permissions = ("stock.manage_stocks",)
        description = "Deletes stocks in bulk"
        error_type_class = StockError
        error_type_field = "stock_error"
