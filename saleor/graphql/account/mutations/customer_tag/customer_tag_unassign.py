from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....account.error_codes import CustomerTagErrorCode
from .....core.tracing import traced_atomic_transaction
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_324, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import CustomerTagError, NonNullList
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import CustomerTag, User

MAX_ASSIGN_ITEMS = 100


class CustomerTagUnassign(BaseMutation):
    users = NonNullList(User, description="The users the tags were unassigned from.")
    customer_tags = NonNullList(
        CustomerTag, description="The customer tags that were unassigned."
    )

    class Arguments:
        user_ids = NonNullList(
            graphene.ID,
            required=True,
            description="IDs of the users to unassign the tags from. Limited to 100.",
        )
        tag_ids = NonNullList(
            graphene.ID,
            required=True,
            description="IDs of the customer tags to unassign. Limited to 100.",
        )

    class Meta:
        description = (
            "Unassign one or more customer tags from one or more users."
            + ADDED_IN_324
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_USERS
        permissions = (AccountPermissions.ASSIGN_CUSTOMER_TAGS,)
        error_type_class = CustomerTagError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_TAG_UNASSIGNED,
                description="One or more tags were unassigned from a user.",
            ),
        ]

    @classmethod
    def clean_input(cls, info: ResolveInfo, user_ids, tag_ids):
        if len(user_ids) > MAX_ASSIGN_ITEMS or len(tag_ids) > MAX_ASSIGN_ITEMS:
            raise ValidationError(
                {
                    "user_ids": ValidationError(
                        f"Cannot unassign more than {MAX_ASSIGN_ITEMS} items at once.",
                        code=CustomerTagErrorCode.INVALID.value,
                    )
                }
            )
        users = cls.get_nodes_or_error(user_ids, "user_ids", User)
        tags = cls.get_nodes_or_error(tag_ids, "tag_ids", CustomerTag)
        return users, tags

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, user_ids, tag_ids
    ):
        users, tags = cls.clean_input(info, user_ids, tag_ids)
        users_by_id = {user.id: user for user in users}
        tags_by_id = {tag.id: tag for tag in tags}

        with traced_atomic_transaction():
            removed = list(
                models.UserCustomerTag.objects.filter(
                    user__in=users, tag__in=tags
                ).values_list("user_id", "tag_id")
            )
            if removed:
                models.UserCustomerTag.objects.filter(
                    user__in=users, tag__in=tags
                ).delete()

        cls.send_events(info, removed, users_by_id, tags_by_id)
        return cls(users=users, customer_tags=tags)

    @classmethod
    def send_events(cls, info: ResolveInfo, removed, users_by_id, tags_by_id):
        if not removed:
            return
        tags_by_user = defaultdict(list)
        for user_id, tag_id in removed:
            tags_by_user[user_id].append(tags_by_id[tag_id])
        manager = get_plugin_manager_promise(info.context).get()
        for user_id, removed_tags in tags_by_user.items():
            cls.call_event(
                manager.customer_tag_unassigned, users_by_id[user_id], removed_tags
            )
