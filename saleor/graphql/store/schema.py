import graphene

from ...core.permissions import StorePermissions
from ..channel.types import ChannelContext
from ..core.fields import PrefetchingConnectionField
from ..decorators import permission_required

from .types import StoreType
from ...store.models import Store, StoreType
from ..core.fields import FilterInputConnectionField
from ..core.types import FilterInputObjectType
from .filters import StoreFilterInput
from .sorters import StoreSortingInput
from .mutations.stores import StoreCreate, StoreDelete, StoreUpdate

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
        id=graphene.Argument(
            graphene.ID, description="ID of the store type.", required=True
        ),
        description="Look up a store type by ID.",
    )

    def resolve_store(self, info, level=None, **kwargs):
        return Store.objects.first()

    def resolve_stores(self, info, level=None, **kwargs):
        return Store.objects.all()


class StoreMutations(graphene.ObjectType):
    # store mutations
    store_create = StoreCreate.Field()
    store_delete = StoreDelete.Field()    
    store_update = StoreUpdate.Field()
