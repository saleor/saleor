import graphene

from ..core.doc_category import DOC_CATEGORY_TAXES
from ..directives import doc
from ..plugins.dataloaders import get_plugin_manager_promise
from . import ResolveInfo
from .mutations import FileUpload
from .types import NonNullList, TaxType


class CoreQueries(graphene.ObjectType):
    tax_types = doc(
        DOC_CATEGORY_TAXES,
        graphene.Field(
            NonNullList(TaxType),
            description="List of all tax rates available from tax gateway.",
            deprecation_reason="Use `taxClasses` field instead.",
        ),
    )

    def resolve_tax_types(self, info: ResolveInfo):
        manager = get_plugin_manager_promise(info.context).get()
        return [
            TaxType(description=tax.description, tax_code=tax.code)
            for tax in manager.get_tax_rate_type_choices()
        ]


class CoreMutations(graphene.ObjectType):
    file_upload = FileUpload.Field()
