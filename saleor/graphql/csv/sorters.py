import graphene

from ..core.types import SortInputObjectType


class JobSortField(graphene.Enum):
    STATUS = "status"
    CREATED_BY = "created_by__id"
    CREATED_AT = "created_at"
    COMPLETED_AT = "completed_at"

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            JobSortField.STATUS,
            JobSortField.CREATED_BY,
            JobSortField.CREATED_AT,
            JobSortField.COMPLETED_AT,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort job by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class JobSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = JobSortField
        type_name = "job"
