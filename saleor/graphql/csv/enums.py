import graphene


class ExportScope(graphene.Enum):
    ALL = "all"
    IDS = "ids"
    FILTER = "filter"
