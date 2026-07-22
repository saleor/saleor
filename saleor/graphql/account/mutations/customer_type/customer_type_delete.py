import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....account.utils import get_default_customer_type
from .....core.tracing import traced_atomic_transaction
from .....permission.enums import CustomerTypePermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_323
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import CustomerTypeDeleteErrorCode
from ....core.mutations import ModelDeleteMutation
from ....core.types import Error
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import CustomerType


class CustomerTypeDeleteError(Error):
    code = CustomerTypeDeleteErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerTypeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            description="ID of the customer type to delete.", required=True
        )

    class Meta:
        description = (
            "Deletes a customer type. Users of the deleted customer type are "
            "reassigned to the default customer type." + ADDED_IN_323
        )
        model = models.CustomerType
        object_type = CustomerType
        permissions = (CustomerTypePermissions.MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES,)
        error_type_class = CustomerTypeDeleteError
        doc_category = DOC_CATEGORY_USERS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_TYPE_DELETED,
                description="A customer type was deleted.",
            ),
        ]

    @classmethod
    def clean_instance(cls, _info: ResolveInfo, instance, /):
        if instance.is_default:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "The default customer type cannot be deleted. Mark "
                        "another customer type as the default first.",
                        code=CustomerTypeDeleteErrorCode.CANNOT_DELETE_DEFAULT.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        customer_type_pk = cls.get_global_id_or_error(
            id, only_type=CustomerType, field="pk"
        )
        with traced_atomic_transaction():
            default_customer_type = get_default_customer_type()
            if str(default_customer_type.pk) != str(customer_type_pk):
                models.User.objects.filter(customer_type_id=customer_type_pk).update(
                    customer_type=default_customer_type
                )
            return super().perform_mutation(_root, info, id=id)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.customer_type_deleted, instance)
