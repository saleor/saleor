import graphene
from ..error_codes import TransferRequestErrorCode as transfer_request_errorcCode
TransferRequestErrorCode = graphene.Enum.from_enum(transfer_request_errorcCode)
