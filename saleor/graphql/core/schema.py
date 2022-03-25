import graphene

from .mutations import FileUpload
from .types import NonNullList, TaxType


class CoreQueries(graphene.ObjectType):
    tax_types = NonNullList(
        TaxType, description="List of all tax rates available from tax gateway."
    )

    def resolve_tax_types(self, info):
        manager = info.context.plugins
        return [
            TaxType(description=tax.description, tax_code=tax.code)
            for tax in manager.get_tax_rate_type_choices()
        ]


class CoreMutations(graphene.ObjectType):
    file_upload = FileUpload.Field()
