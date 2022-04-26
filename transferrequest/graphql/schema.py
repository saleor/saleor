import graphene

from .mutations import TransferRequestCreate, TransferRequestUpdate
from .types import TransferRequest, TransferRequestCountableConnection
from saleor.graphql.core.utils import from_global_id_or_error
from .resolvers import resolve_transferrequest, resolve_transferrequests
from saleor.graphql.core.fields import FilterConnectionField
from .filters import TransferRequestInput
from saleor.graphql.core.connection import create_connection_slice, \
    filter_connection_queryset


class TransferRequestQueries(graphene.ObjectType):
    transfer_request = graphene.Field(TransferRequest,
                                      description="Look up a warehouse by ID.",
                                      id=graphene.Argument(
                                          graphene.ID, description="ID of an transferrequest",
                                          required=True
                                      ), )
    transfer_requests = FilterConnectionField(TransferRequestCountableConnection,
                                              filter=TransferRequestInput(),
                                              description="List of transferrequest.")

    def resolve_transfer_request(self, info, **data):
        transferrequest_pk = data.get("id")
        _, id = from_global_id_or_error(transferrequest_pk, TransferRequest)
        return resolve_transferrequest(id)

    def resolve_transfer_requests(self, info, **kwargs):
        qs = resolve_transferrequests()
        qs = filter_connection_queryset(qs, **kwargs)
        return create_connection_slice(qs, info, kwargs,
                                       TransferRequestCountableConnection)


class TransferRequestMutations(graphene.ObjectType):
    create_transfer_request = TransferRequestCreate.Field()
    approve_transfer_request = TransferRequestUpdate.Field()
