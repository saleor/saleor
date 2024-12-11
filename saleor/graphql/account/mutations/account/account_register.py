import graphene
from django.conf import settings
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from .....account import models
from .....account.error_codes import AccountErrorCode
from .....account.tasks import finish_creating_user
from .....account.utils import RequestorAwareContext
from .....core.utils.url import validate_storefront_url
from .....webhook.event_types import WebhookEventAsyncType
from ....channel.utils import clean_channel
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import LanguageCodeEnum
from ....core.mutations import ModelMutation
from ....core.types import AccountError, NonNullList
from ....core.utils import WebhookEventInfo
from ....meta.inputs import MetadataInput
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
        # we don't want to return id's as it will allow to deduce if user exists
        if response.user:
            response.user.RETURN_ID_IN_API_RESPONSE = False
        return response

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        site = get_site_promise(info.context).get()
        if not site.settings.enable_account_confirmation_by_email:
            return super().clean_input(info, instance, data, **kwargs)
        if not data.get("redirect_url"):
            raise ValidationError(
                {
                    "redirect_url": ValidationError(
                        "This field is required.", code=AccountErrorCode.REQUIRED.value
                    )
                }
            )

        try:
            validate_storefront_url(data["redirect_url"])
        except ValidationError as e:
            raise ValidationError(
                {
                    "redirect_url": ValidationError(
                        e.message, code=AccountErrorCode.INVALID.value
                    )
                }
            ) from e

        data["channel"] = clean_channel(
            data.get("channel"), error_class=AccountErrorCode, allow_replica=False
        ).slug

        data["email"] = data["email"].lower()

        password = data["password"]
        try:
            password_validation.validate_password(password, instance)
        except ValidationError as e:
            raise ValidationError({"password": e}) from e

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
        context_data = RequestorAwareContext.create_context_data(info.context)
        cls.save_and_create_task(user_exists, instance, cleaned_input, context_data)
        return cls.success_response(instance)

    @classmethod
    def save_and_create_task(cls, user_exists, instance, cleaned_input, context_data):
        instance.set_password(cleaned_input["password"])
        instance.is_confirmed = False

        if not user_exists:
            instance.save()

        # moving logic to async task to prevent timing attacks
        finish_creating_user.delay(
            instance.pk if not user_exists else None,
            cleaned_input.get("redirect_url"),
            cleaned_input.get("channel"),
            context_data,
        )

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
