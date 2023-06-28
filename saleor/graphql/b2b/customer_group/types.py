import graphene
from graphene import relay
from ..filters import CategoryDiscountFilter
from ...core import ResolveInfo
from ....permission.enums import AccountPermissions, DiscountPermissions
from ...core.fields import PermissionsField, FilterConnectionField
from ...account.sorters import UserSortingInput
from ...account.schema import CustomerFilterInput
from ...core.types import ModelObjectType, FilterInputObjectType
from ...channel.types import Channel
from ...account.types import UserCountableConnection
from ..category_discount.types import CategoryDiscountCountableConnection
from ...core.connection import CountableConnection, create_connection_slice, filter_connection_queryset
from ....b2b import models
from ....account.models import User


class CategoryDiscountFilterInput(FilterInputObjectType):
    filterset_class = CategoryDiscountFilter

class CustomerGroup(ModelObjectType[models.CustomerGroup]):
    id = graphene.GlobalID()
    name = graphene.String()
    category_discounts = FilterConnectionField(
        CategoryDiscountCountableConnection,
        filter = CategoryDiscountFilterInput(),
        permissions=[
            AccountPermissions.MANAGE_USERS, DiscountPermissions.MANAGE_DISCOUNTS
        ],
    )
    channel = graphene.Field(Channel)
    cusotmers = FilterConnectionField(
        UserCountableConnection,
        filter=CustomerFilterInput(description="Filtering options for customers."),
        sort_by=UserSortingInput(description="Sort customers."),
        description="List of the shop's customers.",
        permissions=[AccountPermissions.MANAGE_USERS],
    ), 

    class Meta:
        description = "Represents customer group data"
        interfaces = [relay.Node]
        model = models.CustomerGroup

    @staticmethod
    def resolve_category_discounts(root: models.CustomerGroup, info: ResolveInfo, **kwargs):
        qs = root.category_discounts.all()
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, CategoryDiscountCountableConnection)
    
    @staticmethod
    def resolve_channel(root: models.CustomerGroup, info: ResolveInfo):
        return root.channel
    
    @staticmethod
    def resolve_cusotmers(root: models.CustomerGroup, info: ResolveInfo, **kwargs):
        qs = User.objects.filter(customer_group=root).distinct()
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, UserCountableConnection)
    
class CustomerGroupCountableConnection(CountableConnection):
    class Meta:
        node = CustomerGroup