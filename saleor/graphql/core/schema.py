import graphene
import graphql_jwt

from ...core.taxes import interface as tax_interface
from .mutations import CreateToken, VerifyToken
from .types.common import TaxType


class CoreMutations(graphene.ObjectType):
    token_create = CreateToken.Field()
    token_refresh = graphql_jwt.Refresh.Field()
    token_verify = VerifyToken.Field()


class CoreQueries(graphene.ObjectType):
    tax_types = graphene.List(
        TaxType, description="List of all tax rates available from tax gateway"
    )

    def resolve_tax_types(self, _info):
        return [
            TaxType(description=tax.description, tax_code=tax.code)
            for tax in tax_interface.get_tax_rate_type_choices()
        ]
