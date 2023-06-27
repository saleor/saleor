import graphene
from graphene import relay
from ...core import ResolveInfo
from ...core.connection import CountableConnection
from ...core.types.common import CountryDisplay
from ...core.types import ModelObjectType
from ...account.types import User
from ....b2b import models

class CompanyInfo(ModelObjectType[models.CompanyInfo]):
    id = graphene.GlobalID()
    customer = graphene.Field(User)
    company_name = graphene.String()
    street_address_1 = graphene.String()
    street_address_2 = graphene.String()
    city = graphene.String()
    postal_code = graphene.String()
    country = graphene.Field(CountryDisplay)
    personal_phone = graphene.String()
    business_phone = graphene.String()
    uid = graphene.String()
    comment = graphene.String()
    has_access_to_b2b = graphene.Boolean()
    recieved_at = graphene.DateTime()


    class Meta:
        description = "Represents company data"
        interfaces = [relay.Node]
        model = models.CompanyInfo


    @staticmethod
    def resolve_customer(root: models.CompanyInfo, _info: ResolveInfo):
        return root.customer

    @staticmethod
    def resolve_country(root: models.CompanyInfo, _info: ResolveInfo):
        return CountryDisplay(code=root.country.code, country=root.country.name)
    
    @staticmethod
    def recieved_at(root: models.CompanyInfo, _info: ResolveInfo):
        return root.recieved_at
    
class CompanyInfoCountableConnection(CountableConnection):
    class Meta:
        node = CompanyInfo

