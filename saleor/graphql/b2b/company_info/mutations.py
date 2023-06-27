import graphene
from .types import CompanyInfo
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...account.enums import CountryCodeEnum
from ...account.types import User
from ....b2b import models
from ....permission.enums import AccountPermissions
from ....permission.auth_filters import AuthorizationFilters
from ...core.types import AccountError

class CompanyInfoInput(graphene.InputObjectType):
    company_name = graphene.String()
    street_address = graphene.String()
    postal_code = graphene.String()
    city = graphene.String()
    country = CountryCodeEnum()
    personal_phone = graphene.String()
    business_phone = graphene.String()
    comment = graphene.String()
    uid = graphene.String()

class B2BResponseInput(graphene.InputObjectType):
    has_access_to_b2b = graphene.Boolean()

class RequestB2BAccess(ModelMutation):
    class Arguments:
        input = CompanyInfoInput(
            required=True
        )

    class Meta:
        description = "Request b2b access by filling up company information"
        model = models.CompanyInfo
        object_type = CompanyInfo
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        customer = info.context.user
        instance.customer = customer
        instance.save()


class CompanyInfoUpdate(ModelMutation):
    class Arguments:
        id = graphene.Argument(graphene.ID, required=True)
        input = CompanyInfoInput(
            required=True
        )
    
    class Meta:
        description = "Update company information"
        model = models.CompanyInfo
        object_type = CompanyInfo
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, input):
        user = info.context.user
        if instance.customer != user:
            raise Exception(
                "Company Info does not belong to logged in user"
            )
        cleaned_input = input
        return cleaned_input
    

class ResponseForB2BRequest(ModelMutation):
    class Arguments:
        id = graphene.Argument(graphene.ID, required=True)
        input = B2BResponseInput(required=True)

    class Meta:
        description = "Response for b2b access request"
        model = models.CompanyInfo
        object_type = CompanyInfo
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"  