from urllib.parse import urlencode

import graphene
from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError

from .....account import events as account_events
from .....account import models, notifications, search
from .....account.error_codes import AccountErrorCode
from .....core.tracing import traced_atomic_transaction
from .....core.utils.url import prepare_url, validate_storefront_url
from .....webhook.event_types import WebhookEventAsyncType
from ....channel.utils import clean_channel
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import LanguageCodeEnum
from ....core.mutations import ModelMutation
from ....core.types import AccountError, NonNullList
from ....core.utils import WebhookEventInfo
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ....site.dataloaders import get_site_promise
from ...types import User
from .base import AccountBaseInput


class AccountRegisterInput(AccountBaseInput):
    email = graphene.String(description="The email address of the user.", required=True)
    password = graphene.String(description="Password.", required=True)
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    redirect_url = graphene.String(
        description=(
            "Base of frontend URL that will be needed to create confirmation URL. "
            "Required when account confirmation is enabled."
        ),
        required=False,
    )
    language_code = graphene.Argument(
        LanguageCodeEnum, required=False, description="User language code."
    )
    metadata = NonNullList(
        MetadataInput,
        description="User public metadata.",
        required=False,
    )
    channel = graphene.String(
        description=(
            "Slug of a channel which will be used to notify users. Optional when "
            "only one channel exists."
        )
    )

    class Meta:
        description = "Fields required to create a user."
        doc_category = DOC_CATEGORY_USERS


class AccountRegister(ModelMutation):
    class Arguments:
        input = AccountRegisterInput(
            description="Fields required to create a user.", required=True
        )

    requires_confirmation = graphene.Boolean(
        description="Informs whether users need to confirm their email address."
    )

    class Meta:
        description = "Register a new user."
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"
        model = models.User
        object_type = User
        support_meta_field = True
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_CREATED,
                description="A new customer account was created.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for account confirmation.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ACCOUNT_CONFIRMATION_REQUESTED,
                description=(
                    "An user confirmation was requested. "
                    "This event is always sent regardless of settings."
                ),
            ),
        ]

    @classmethod
    def mutate(cls, root, info: ResolveInfo, **data):
        site = get_site_promise(info.context).get()
        response = super().mutate(root, info, **data)
        response.requires_confirmation = (
            site.settings.enable_account_confirmation_by_email
        )
        # we don't want to leak id's as it will allow to deduce if user exists
        if response.user:
            response.user.DO_NOT_LEAK_ID = True
        return response

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        site = get_site_promise(info.context).get()
        if not site.settings.enable_account_confirmation_by_email:
            return super().clean_input(info, instance, data, **kwargs)
        elif not data.get("redirect_url"):
            raise ValidationError(
                {
                    "redirect_url": ValidationError(
                        "This field is required.", code=AccountErrorCode.REQUIRED.value
                    )
                }
            )

        try:
            validate_storefront_url(data["redirect_url"])
        except ValidationError as error:
            raise ValidationError(
                {
                    "redirect_url": ValidationError(
                        error.message, code=AccountErrorCode.INVALID.value
                    )
                }
            )

        data["channel"] = clean_channel(
            data.get("channel"), error_class=AccountErrorCode, allow_replica=False
        ).slug

        data["email"] = data["email"].lower()

        password = data["password"]
        try:
            password_validation.validate_password(password, instance)
        except ValidationError as error:
            raise ValidationError({"password": error})

        data["language_code"] = data.get("language_code", settings.LANGUAGE_CODE)
        return super().clean_input(info, instance, data, **kwargs)

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance, /):
        user_exists = False

        try:
            instance.full_clean(exclude=["password"])
        except ValidationError as error:
            user_exists, error.error_dict = cls._clean_errors(error)

            if error.error_dict:
                raise error

        return user_exists

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = models.User()
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        metadata_list = cleaned_input.pop("metadata", None)
        private_metadata_list = cleaned_input.pop("private_metadata", None)

        instance = cls.construct_instance(instance, cleaned_input)
        cls.validate_and_update_metadata(instance, metadata_list, private_metadata_list)
        user_exists = cls.clean_instance(info, instance)
        if not user_exists:
            cls.save(info, instance, cleaned_input)
        return cls.success_response(instance)

    @classmethod
    def save(cls, info: ResolveInfo, user, cleaned_input):
        password = cleaned_input["password"]
        user.set_password(password)
        user.search_document = search.prepare_user_search_document_value(
            user, attach_addresses_data=False
        )
        manager = get_plugin_manager_promise(info.context).get()
        site = get_site_promise(info.context).get()
        token = None
        redirect_url = cleaned_input.get("redirect_url")

        with traced_atomic_transaction():
            user.is_confirmed = False
            user.save()
            if site.settings.enable_account_confirmation_by_email:
                # Notifications will be deprecated in the future
                token = default_token_generator.make_token(user)
                notifications.send_account_confirmation(
                    user,
                    redirect_url,
                    manager,
                    channel_slug=cleaned_input["channel"],
                    token=token,
                )
                if redirect_url:
                    params = urlencode(
                        {
                            "email": user.email,
                            "token": token or default_token_generator.make_token(user),
                        }
                    )
                    redirect_url = prepare_url(params, redirect_url)

                cls.call_event(
                    manager.account_confirmation_requested,
                    user,
                    cleaned_input["channel"],
                    token,
                    redirect_url,
                )

            cls.call_event(manager.customer_created, user)
        account_events.customer_account_created_event(user=user)

    @classmethod
    def _clean_email_errors(cls, errors):
        """Clean email errors.

        Iterates over errors for field `email` with purpose to
        not leak `unique` error in case when user already exists in database which would
        allow user enumeration.
        Returns boolean value if user exists and filtered errors
        that can be displayed to the end user.
        """
        existing_user = False
        filtered_errors = []

        for error in errors:
            if error.code == "unique":
                existing_user = True
                continue
            filtered_errors.append(error)

        return existing_user, filtered_errors

    @classmethod
    def _clean_errors(cls, error):
        """Clean errors.

        Iterate over errors for field `email` with purpose to
        not leak error indicating user existence in the system.
        Returns boolean value if user exists and filtered errors
        that can be displayed to the end user.
        """
        existing_user = False
        error_dict = {}

        for field, errors in error.error_dict.items():
            if field == "email":
                existing_user, errors = cls._clean_email_errors(errors)
                if not errors:
                    continue

            error_dict[field] = errors

        return existing_user, error_dict
