import graphene

from ..core.types import SortInputObjectType


class WebhookSortField(graphene.Enum):
    NAME = ["name", "pk"]
    SERVICE_ACCOUNT = ["app__name", "name", "pk"]
    TARGET_URL = ["target_url", "name", "pk"]
    APP = ["app__name", "name", "pk"]

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            WebhookSortField.NAME,
            WebhookSortField.SERVICE_ACCOUNT,
            WebhookSortField.TARGET_URL,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort webhooks by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class WebhookSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = WebhookSortField
        type_name = "webhooks"
