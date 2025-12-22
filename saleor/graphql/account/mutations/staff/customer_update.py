from typing import cast

import graphene
from django.db.models import QuerySet

from .....account import events as account_events
from .....account import models
from .....account.search import prepare_user_search_document_value
from .....core.tracing import traced_atomic_transaction
from .....core.utils.update_mutation_manager import InstanceTracker
from .....giftcard.search import mark_gift_cards_search_index_as_dirty
from .....giftcard.utils import assign_user_gift_cards, get_user_gift_cards
from .....order.utils import match_orders_with_new_user
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import User
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import ModelWithExtRefMutation
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ....site.dataloaders import get_site_promise
from ..base import BaseCustomerCreate, CustomerInput
from .utils import CUSTOMER_UPDATE_FIELDS


class CustomerUpdate(BaseCustomerCreate, ModelWithExtRefMutation):
    class Arguments:
        id = graphene.ID(description="ID of a customer to update.", required=False)
        external_reference = graphene.String(
            required=False,
            description="External ID of a customer to update.",
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

    FIELDS_TO_TRACK = list(CUSTOMER_UPDATE_FIELDS)

    @classmethod
    def generate_events(
        cls,
        info: ResolveInfo,
        instance: models.User,
        instance_tracker: InstanceTracker,
        modified_instance_fields: set,
    ):
        # Retrieve the event base data
        staff_user = info.context.user
        app = get_app_promise(info.context).get()

        # Compare the data
        previous_active = instance_tracker.initial_instance_values.get("is_active")
        previous_confirmed = instance_tracker.initial_instance_values.get(
            "is_confirmed"
        )
        was_activated = not previous_active and instance.is_active
        was_deactivated = previous_active and not instance.is_active
        being_confirmed = not previous_confirmed and instance.is_confirmed

        if "email" in modified_instance_fields or being_confirmed:
            assign_user_gift_cards(instance)
            match_orders_with_new_user(instance)

        # Generate the events accordingly
        if "email" in modified_instance_fields:
            account_events.assigned_email_to_a_customer_event(
                staff_user=staff_user, app=app, new_email=instance.email
            )
        if (
            "first_name" in modified_instance_fields
            or "last_name" in modified_instance_fields
        ):
            account_events.assigned_name_to_a_customer_event(
                staff_user=staff_user, app=app, new_name=instance.get_full_name()
            )
        if was_activated:
            account_events.customer_account_activated_event(
                staff_user=info.context.user,
                app=app,
                account_id=instance.id,
            )
        if was_deactivated:
            account_events.customer_account_deactivated_event(
                staff_user=info.context.user,
                app=app,
                account_id=instance.id,
            )

    @classmethod
    def update_gift_card_search_vector(
        cls,
        instance: models.User,
        instance_tracker: InstanceTracker,
        gift_cards: QuerySet,
    ):
        has_new_name = (
            instance_tracker.initial_instance_values.get("first_name")
            != instance.first_name
            or instance_tracker.initial_instance_values.get("last_name")
            != instance.last_name
        )
        has_new_email = (
            instance_tracker.initial_instance_values.get("email") != instance.email
        )
        if has_new_email or has_new_name:
            mark_gift_cards_search_index_as_dirty(gift_cards)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        """Generate events by comparing the old instance with the new data.

        It overrides the `perform_mutation` base method of ModelMutation.
        """
        with traced_atomic_transaction():
            # Retrieve the data
            instance = cls.get_instance(info, **data)
            instance = cast(models.User, instance)
            instance_tracker = InstanceTracker(instance, cls.FIELDS_TO_TRACK)
            input_data = data.get("input")
            gift_cards = get_user_gift_cards(instance)

            # Clean the input and generate a new instance from the new data
            cleaned_input = cls.clean_input(info, instance, input_data)
            metadata_list: list[MetadataInput] = cleaned_input.pop("metadata", None)
            private_metadata_list: list[MetadataInput] = cleaned_input.pop(
                "private_metadata", None
            )

            metadata_collection = cls.create_metadata_from_graphql_input(
                metadata_list, error_field_name="metadata"
            )
            private_metadata_collection = cls.create_metadata_from_graphql_input(
                private_metadata_list, error_field_name="private_metadata"
            )

            instance = cls.construct_instance(instance, cleaned_input)
            cls.validate_and_update_metadata(
                instance, metadata_collection, private_metadata_collection
            )

            # Save the new instance data
            cls.clean_instance(info, instance)
            non_metadata_modified_fields, metadata_modified_fields = cls._save(
                info, instance, cleaned_input, instance_tracker
            )
            cls._save_m2m(info, instance, cleaned_input)

            cls.generate_events(
                info, instance, instance_tracker, non_metadata_modified_fields
            )

        if non_metadata_modified_fields or metadata_modified_fields:
            site = get_site_promise(info.context).get()
            use_legacy_webhooks_emission = (
                site.settings.use_legacy_update_webhook_emission
            )
            manager = get_plugin_manager_promise(info.context).get()
            if non_metadata_modified_fields or (
                metadata_modified_fields and use_legacy_webhooks_emission
            ):
                cls.call_event(manager.customer_updated, instance)

            if metadata_modified_fields:
                cls.call_event(manager.customer_metadata_updated, instance)

        if gift_cards:
            cls.update_gift_card_search_vector(instance, instance_tracker, gift_cards)

        # Return the response
        return cls.success_response(instance)

    @classmethod
    def _save(
        cls, info: ResolveInfo, instance, cleaned_input, instance_tracker
    ) -> tuple[set, set]:
        instance = cast(models.User, instance_tracker.instance)
        modified_instance_fields = set(instance_tracker.get_modified_fields())
        metadata_modified_fields = {
            "metadata",
            "private_metadata",
        } & modified_instance_fields

        if changed_fields := cls.save_default_addresses(
            cleaned_input=cleaned_input,
            user_instance=instance,
        ):
            modified_instance_fields.update(changed_fields)

        non_metadata_modified_fields = (
            set(modified_instance_fields) - metadata_modified_fields
        )
        if non_metadata_modified_fields:
            instance.search_document = prepare_user_search_document_value(instance)
            modified_instance_fields.add("search_document")

        if modified_instance_fields:
            modified_instance_fields.add("updated_at")
            instance.save(update_fields=list(modified_instance_fields))

        return non_metadata_modified_fields, metadata_modified_fields

    @classmethod
    def get_instance(cls, info, **data):
        """Retrieve an instance from the supplied global id.

        Ensure that `User` object will be locked in order to prevent simultaneous updates
        mutually overwriting each other's changes.
        """
        object_id = cls.get_object_id(**data)
        qs = models.User.objects.all().select_for_update()

        if object_id:
            return cls.get_node_or_error(info, object_id, only_type=User, qs=qs)
        return None
