import graphene
from saleor.graphql.core.mutations import BaseMutation, ModelDeleteMutation, \
    ModelMutation
from transferrequest import models
from saleor.graphql.core.types.common import Error
from .enums import TransferRequestErrorCode
from .types import TransferRequest


class TransferRequestError(Error):
    code = TransferRequestErrorCode(description="The error code.", required=True)


class TransferRequestCreateInput(graphene.InputObjectType):
    warehouse_origin = graphene.Int(description="")
    warehouse_destinate = graphene.Int(description="")
    product_variant_id = graphene.Int(description="")
    quantity = graphene.Int(description="")


class TransferRequestUpdateInput(graphene.InputObjectType):
    approved = graphene.Boolean(description="status", required=True)


class TransferRequestCreate(ModelMutation):
    class Arguments:
        input = TransferRequestCreateInput(required=True, description="")

    class Meta:
        description = "Create new Transfer request"
        model = models.TransferRequest
        object_type = TransferRequest
        error_type_class = TransferRequestError


class TransferRequestUpdate(ModelMutation):
    class Meta:
        description = "Update Transfer request"
        model = models.TransferRequest
        object_type = TransferRequest
        error_type_class = TransferRequestError

    class Arguments:
        id = graphene.ID(description="ID of a warehouse to update.", required=True)
        input = TransferRequestUpdateInput(description="", required=True)
