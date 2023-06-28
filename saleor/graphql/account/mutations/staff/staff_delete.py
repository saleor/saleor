import graphene

from .....account import models
from .....account.utils import remove_staff_member
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import User
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import StaffError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ..base import StaffDeleteMixin
from .base import UserDelete


class StaffDelete(StaffDeleteMixin, UserDelete):
    class Meta:
        description = (
            "Deletes a staff user. Apps are not allowed to perform this mutation."
        )
        doc_category = DOC_CATEGORY_USERS
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = StaffError
        error_type_field = "staff_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.STAFF_DELETED,
                description="A staff account was deleted.",
            ),
        ]

    class Arguments:
        id = graphene.ID(required=True, description="ID of a staff user to delete.")

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        instance = cls.get_node_or_error(info, id, only_type=User)
        cls.clean_instance(info, instance)

        db_id = instance.id
        remove_staff_member(instance)
        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id

        response = cls.success_response(instance)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.staff_deleted, instance)

        return response
