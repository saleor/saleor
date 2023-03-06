import graphene

from .mutations import TaxExemptionManage


class TaxMutations(graphene.ObjectType):
    tax_exemption_manage = TaxExemptionManage.Field()
