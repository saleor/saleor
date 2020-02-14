import graphene

from ...csv import JobStatus
from ...graphql.core.enums import to_enum


class ExportScope(graphene.Enum):
    ALL = "all"
    IDS = "ids"
    FILTER = "filter"


JobStatusEnum = to_enum(JobStatus)
