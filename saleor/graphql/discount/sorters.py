import graphene

from ..core.types import SortInputObjectType


class SaleSortField(graphene.Enum):
    NAME = "name"
    START_DATE = "start_date"
    END_DATE = "end_date"
    VALUE = "value"
    TYPE = "type"

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            SaleSortField.NAME,
            SaleSortField.START_DATE,
            SaleSortField.END_DATE,
            SaleSortField.VALUE,
            SaleSortField.TYPE,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort sales by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class SaleSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = SaleSortField
        type_name = "sales"
