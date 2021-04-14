import graphene

from ...core.permissions import StorePermissions
from ..channel.types import ChannelContext
from ..core.fields import PrefetchingConnectionField
from ..decorators import permission_required

from .types import Store, StoreType
from ..core.fields import FilterInputConnectionField
from ..core.types import FilterInputObjectType
from .filters import StoreFilterInput
from .sorters import StoreSortingInput
from .mutations.stores import (
    StoreCreate,
    StoreDelete,
    StoreUpdate,
    StoreTypeCreate,
    StoreTypeDelete,
    StoreTypeUpdate,
)
from .resolvers import (
    resolve_store,
    resolve_stores,
    resolve_store_type,
    resolve_store_types,
)

class StoreQueries(graphene.ObjectType):
    store = graphene.Field(
        Store,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the store.",
        ),
        description="Look up a store by ID.",
    )

    stores = FilterInputConnectionField(
        Store,
        filter=StoreFilterInput(description="Filtering options for store."),
        sort_by=StoreSortingInput(description="Sort store."),
        description="List of the store.",
    )

    store_type = graphene.Field(
        StoreType,
        id=graphene.Argument(graphene.ID, description="ID of the store type."),
        description="Look up a store type by ID or slug.",
    )

    store_types = FilterInputConnectionField(
        StoreType,        
        description="List of the shop's categories.",
    )

    def resolve_store(self, info, id=None, slug=None):
        return resolve_store(info, id, slug)

    def resolve_stores(self, info, **kwargs):
        return resolve_stores(info, **kwargs)

    def resolve_store_type(self, info, id):
        return resolve_store_type(info, id)

    def resolve_store_types(self, info, **kwargs):
        return resolve_store_types(info, **kwargs)


class StoreMutations(graphene.ObjectType):
    # store mutations
    store_create = StoreCreate.Field()
    store_delete = StoreDelete.Field()
    store_update = StoreUpdate.Field()

    # store type mutations
    store_type_create = StoreTypeCreate.Field()
    store_type_delete = StoreTypeDelete.Field()
    store_type_update = StoreTypeUpdate.Field()
