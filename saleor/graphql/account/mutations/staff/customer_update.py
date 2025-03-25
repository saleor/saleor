from copy import copy
from urllib.parse import urlencode

import graphene
from django.contrib.auth.tokens import default_token_generator
from django.db.models import QuerySet

from .....account import events as account_events
from .....account import models
from .....account.error_codes import AccountErrorCode
from .....account.notifications import send_set_password_notification
from .....account.search import prepare_user_search_document_value
from .....core.tracing import traced_atomic_transaction
from .....core.utils.url import prepare_url
from .....giftcard.search import mark_gift_cards_search_index_as_dirty
from .....giftcard.utils import assign_user_gift_cards, get_user_gift_cards
from .....order.utils import match_orders_with_new_user
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import User
from ....app.dataloaders import get_app_promise
from ....channel.utils import clean_channel, validate_channel
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import ModelWithExtRefMutation
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ..base import BILLING_ADDRESS_FIELD, SHIPPING_ADDRESS_FIELD, CustomerInput
from .customer_create import CustomerCreate


class CustomerUpdate(CustomerCreate, ModelWithExtRefMutation):
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

        new_instance = cls.construct_instance(copy(original_instance), cleaned_input)
        cls.validate_and_update_metadata(
            new_instance, metadata_collection, private_metadata_collection
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

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        default_shipping_address = cleaned_input.get(SHIPPING_ADDRESS_FIELD)
        manager = get_plugin_manager_promise(info.context).get()
        if default_shipping_address:
            default_shipping_address.save()
            instance.default_shipping_address = default_shipping_address
        default_billing_address = cleaned_input.get(BILLING_ADDRESS_FIELD)
        if default_billing_address:
            default_billing_address.save()
            instance.default_billing_address = default_billing_address

        is_creation = instance.pk is None
        super().save(info, instance, cleaned_input)
        if default_billing_address:
            instance.addresses.add(default_billing_address)
        if default_shipping_address:
            instance.addresses.add(default_shipping_address)

        instance.search_document = prepare_user_search_document_value(instance)
        instance.save(update_fields=["search_document", "updated_at"])

        # The instance is a new object in db, create an event
        if is_creation:
            cls.call_event(manager.customer_created, instance)
            account_events.customer_account_created_event(user=instance)
        else:
            cls.call_event(manager.customer_updated, instance)

        if redirect_url := cleaned_input.get("redirect_url"):
            channel_slug = cleaned_input.get("channel")
            if not instance.is_staff:
                channel_slug = clean_channel(
                    channel_slug, error_class=AccountErrorCode, allow_replica=False
                ).slug
            elif channel_slug is not None:
                channel_slug = validate_channel(
                    channel_slug, error_class=AccountErrorCode
                ).slug
            send_set_password_notification(
                redirect_url,
                instance,
                manager,
                channel_slug,
            )
            token = default_token_generator.make_token(instance)
            params = urlencode({"email": instance.email, "token": token})
            cls.call_event(
                manager.account_set_password_requested,
                instance,
                channel_slug,
                token,
                prepare_url(params, redirect_url),
            )
