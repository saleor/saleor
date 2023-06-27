import graphene
from ..core.fields import ConnectionField
from ...permission.enums import AccountPermissions, DiscountPermissions
from ..core.connection import create_connection_slice
from ..core.validators import validate_one_of_args_is_in_query
from ..core.utils import from_global_id_or_error
from ...b2b import models
from .customer_group.mutations import *
from .customer_group.types import *
from .category_discount.types import *
from .company_info.types import *
from .category_discount.mutations import *
from .company_info.mutations import *


class B2BQueries(graphene.ObjectType):
    company_info = PermissionsField(CompanyInfo, id=graphene.Argument(graphene.ID, required=True), permissions=[AccountPermissions.MANAGE_USERS],)
    company_infos = PermissionsField(CompanyInfoCountableConnection, permissions=[AccountPermissions.MANAGE_USERS,])
    customer_group = PermissionsField(CustomerGroup, id=graphene.Argument(graphene.ID, required=True), permissions=[AccountPermissions.MANAGE_USERS, DiscountPermissions.MANAGE_DISCOUNTS])
    customer_groups = PermissionsField(CustomerGroupCountableConnection, permissions=[AccountPermissions.MANAGE_USERS, DiscountPermissions.MANAGE_DISCOUNTS])

    @staticmethod
    def resolve_company_info(_root, info: ResolveInfo, id=None):
        if id:
            _, id = from_global_id_or_error(id, CompanyInfo)
            return models.CompanyInfo.objects.filter(id=id).first()
        else: 
            return None
    
    @staticmethod
    def resolve_comapny_infos(_root, info: ResolveInfo, **kwargs):
        qs = models.CompanyInfo.objects.all()
        return create_connection_slice(qs, info, kwargs, CompanyInfoCountableConnection)
    
    @staticmethod
    def resolve_customer_group(_root, info: ResolveInfo, id=None):
        if id:
            _, id = from_global_id_or_error(id, CustomerGroup)
            return models.CustomerGroup.objects.filter(id=id).first()
        else: 
            return None
    
    @staticmethod
    def resolve_customer_groups(root, info: ResolveInfo, **kwargs):
        qs = models.CustomerGroup.objects.all()
        return create_connection_slice(qs, info, kwargs, CustomerGroupCountableConnection)


class B2BMutations(graphene.ObjectType):
    request_b2b_access = RequestB2BAccess.Field()
    update_company_info = CompanyInfoUpdate.Field()
    response_b2b_access = ResponseForB2BRequest.Field()

    create_customer_group = CreateCustomerGroup.Field()
    update_customer_group = UpdateCustomerGroup.Field()
    add_customers_to_group = AppointCustomersToGroup.Field()
    remove_customers_to_group = RemoveCustomersFromGroup.Field()
    delete_customer_group = DeleteCustomerGroup.Field()

    create_category_discount_and_add_to_group = CreateDiscountAndAddToGroup.Field()
    update_category_discount = UpdateCategoryDiscount.Field()
    delete_category_discount= DeleteCategoryDiscount.Field()



