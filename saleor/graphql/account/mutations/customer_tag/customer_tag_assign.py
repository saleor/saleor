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
from ....utils import get_user_or_app_from_context
from ...types import CustomerTag, User

MAX_ASSIGN_ITEMS = 100


class CustomerTagAssign(BaseMutation):
    users = NonNullList(User, description="The users the tags were assigned to.")
    customer_tags = NonNullList(
        CustomerTag, description="The customer tags that were assigned."
    )

    class Arguments:
        user_ids = NonNullList(
            graphene.ID,
            required=True,
            description="IDs of the users to assign the tags to. Limited to 100.",
        )
        tag_ids = NonNullList(
            graphene.ID,
            required=True,
            description="IDs of the customer tags to assign. Limited to 100.",
        )

    class Meta:
        description = (
            "Assign one or more customer tags to one or more users."
            + ADDED_IN_324
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_USERS
        permissions = (AccountPermissions.ASSIGN_CUSTOMER_TAGS,)
        error_type_class = CustomerTagError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_TAG_ASSIGNED,
                description="One or more tags were assigned to a user.",
            ),
        ]

    @classmethod
    def clean_input(cls, info: ResolveInfo, user_ids, tag_ids):
        if len(user_ids) > MAX_ASSIGN_ITEMS or len(tag_ids) > MAX_ASSIGN_ITEMS:
            raise ValidationError(
                {
                    "user_ids": ValidationError(
                        f"Cannot assign more than {MAX_ASSIGN_ITEMS} items at once.",
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
        requestor = get_user_or_app_from_context(info.context)
        assigned_by = requestor if isinstance(requestor, models.User) else None

        with traced_atomic_transaction():
            # Lock the tags so concurrent assignments touching the same tag are
            # serialized. This makes the existence check below authoritative, so
            # each genuinely new assignment emits exactly one event (a losing
            # racer sees the row already present and skips it).
            list(
                models.CustomerTag.objects.order_by("pk")
                .select_for_update(of=["self"])
                .filter(pk__in=[tag.pk for tag in tags])
            )
            existing = set(
                models.UserCustomerTag.objects.filter(
                    user__in=users, tag__in=tags
                ).values_list("user_id", "tag_id")
            )
            to_create = [
                models.UserCustomerTag(user=user, tag=tag, assigned_by=assigned_by)
                for user in users
                for tag in tags
                if (user.id, tag.id) not in existing
            ]
            if to_create:
                models.UserCustomerTag.objects.bulk_create(
                    to_create, ignore_conflicts=True
                )

        cls.send_events(info, to_create)
        return cls(users=users, customer_tags=tags)

    @classmethod
    def send_events(cls, info: ResolveInfo, assignments):
        if not assignments:
            return
        tags_by_user = defaultdict(list)
        for assignment in assignments:
            tags_by_user[assignment.user].append(assignment.tag)
        manager = get_plugin_manager_promise(info.context).get()
        for user, tags in tags_by_user.items():
            cls.call_event(manager.customer_tag_assigned, user, tags)
