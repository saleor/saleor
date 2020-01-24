import graphene

from .mutations import ExportProducts


class CsvMutations(graphene.ObjectType):
    export_products = ExportProducts.Field()
