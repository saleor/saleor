import graphene

from ..plugins.dataloaders import get_plugin_manager_promise
from . import ResolveInfo
from .mutations import FileUpload
from .types import NonNullList, TaxType


class CoreQueries(graphene.ObjectType):
    tax_types = NonNullList(
        TaxType, description="List of all tax rates available from tax gateway."
    )

    def resolve_tax_types(self, info: ResolveInfo):
        manager = get_plugin_manager_promise(info.context).get()
        return [
            TaxType(description=tax.description, tax_code=tax.code)
            for tax in manager.get_tax_rate_type_choices()
        ]


class CoreMutations(graphene.ObjectType):
    file_upload = FileUpload.Field()
