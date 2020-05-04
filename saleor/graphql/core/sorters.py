import graphene


class BaseJobSortField(graphene.Enum):
    STATUS = "status"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"

    @property
    def description(self):
        if self.name in BaseJobSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort job by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)
