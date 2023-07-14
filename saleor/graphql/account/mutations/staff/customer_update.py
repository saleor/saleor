from copy import copy

import graphene
from django.db.models import QuerySet

from .....account import events as account_events
from .....account import models
from .....giftcard.search import mark_gift_cards_search_index_as_dirty
from .....giftcard.utils import assign_user_gift_cards, get_user_gift_cards
from .....order.utils import match_orders_with_new_user
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import User
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_310
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import ModelWithExtRefMutation
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ..base import CustomerInput
from .customer_create import CustomerCreate


class CustomerUpdate(CustomerCreate, ModelWithExtRefMutation):
    class Arguments:
        id = graphene.ID(description="ID of a customer to update.", required=False)
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a customer to update. {ADDED_IN_310}",
        )
        input = CustomerInput(
            description="Fields required to update a customer.", required=True
        )

    class Meta:
        description = "Updates an existing customer."
        doc_category = DOC_CATEGORY_USERS
        exclude = ["password"]
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"
        support_meta_field = True
        support_private_meta_field = True
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_UPDATED,
                description="A new customer account was updated.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_METADATA_UPDATED,
                description="Optionally called when customer's metadata was updated.",
            ),
        ]

    @classmethod
    def generate_events(
        cls, info: ResolveInfo, old_instance: models.User, new_instance: models.User
    ):
        # Retrieve the event base data
        staff_user = info.context.user
        app = get_app_promise(info.context).get()
        new_email = new_instance.email
        new_fullname = new_instance.get_full_name()

        # Compare the data
        has_new_name = old_instance.get_full_name() != new_fullname
        has_new_email = old_instance.email != new_email
        was_activated = not old_instance.is_active and new_instance.is_active
        was_deactivated = old_instance.is_active and not new_instance.is_active
        being_confirmed = not old_instance.is_confirmed and new_instance.is_confirmed

        if has_new_email or being_confirmed:
            assign_user_gift_cards(new_instance)
            match_orders_with_new_user(new_instance)

        # Generate the events accordingly
        if has_new_email:
            account_events.assigned_email_to_a_customer_event(
                staff_user=staff_user, app=app, new_email=new_email
            )
        if has_new_name:
            account_events.assigned_name_to_a_customer_event(
                staff_user=staff_user, app=app, new_name=new_fullname
            )
        if was_activated:
            account_events.customer_account_activated_event(
                staff_user=info.context.user,
                app=app,
                account_id=old_instance.id,
            )
        if was_deactivated:
            account_events.customer_account_deactivated_event(
                staff_user=info.context.user,
                app=app,
                account_id=old_instance.id,
            )

    @classmethod
    def update_gift_card_search_vector(
        cls,
        old_instance: models.User,
        new_instance: models.User,
        gift_cards: QuerySet,
    ):
        new_email = new_instance.email
        new_fullname = new_instance.get_full_name()
        has_new_name = old_instance.get_full_name() != new_fullname
        has_new_email = old_instance.email != new_email
        if has_new_email or has_new_name:
            mark_gift_cards_search_index_as_dirty(gift_cards)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        """Generate events by comparing the old instance with the new data.

        It overrides the `perform_mutation` base method of ModelMutation.
        """

        # Retrieve the data
        original_instance = cls.get_instance(info, **data)
        data = data.get("input")

        # Clean the input and generate a new instance from the new data
        cleaned_input = cls.clean_input(info, original_instance, data)
        metadata_list = cleaned_input.pop("metadata", None)
        private_metadata_list = cleaned_input.pop("private_metadata", None)

        new_instance = cls.construct_instance(copy(original_instance), cleaned_input)
        cls.validate_and_update_metadata(
            new_instance, metadata_list, private_metadata_list
        )

        # Save the new instance data
        cls.clean_instance(info, new_instance)
        cls.save(info, new_instance, cleaned_input)
        cls._save_m2m(info, new_instance, cleaned_input)

        # Generate events by comparing the instances
        cls.generate_events(info, original_instance, new_instance)

        if metadata_list:
            manager = get_plugin_manager_promise(info.context).get()
            cls.call_event(manager.customer_metadata_updated, new_instance)

        if gift_cards := get_user_gift_cards(new_instance):
            cls.update_gift_card_search_vector(
                original_instance, new_instance, gift_cards
            )

        # Return the response
        return cls.success_response(new_instance)
