import graphene
import graphql_jwt

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

    def resolve_tax_types(self, info):
        manager = info.context.extensions
        return [
            TaxType(description=tax.description, tax_code=tax.code)
            for tax in manager.get_tax_rate_type_choices()
        ]
