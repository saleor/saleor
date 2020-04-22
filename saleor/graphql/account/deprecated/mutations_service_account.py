import graphene

from ....app import models
from ....core.permissions import AppPermission, get_permissions
from ...core.enums import PermissionEnum
from ...core.mutations import ModelDeleteMutation, ModelMutation
from ...core.types.common import AccountError
from ...meta.deprecated.mutations import ClearMetaBaseMutation, UpdateMetaBaseMutation
from .types import ServiceAccount, ServiceAccountToken


class ServiceAccountInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the service account.")
    is_active = graphene.Boolean(
        description="Determine if this service account should be enabled."
    )
    permissions = graphene.List(
        PermissionEnum,
        description="List of permission code names to assign to this service account.",
    )


class ServiceAccountTokenInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the token.", required=False)
    service_account = graphene.ID(description="ID of service account.", required=True)


class ServiceAccountTokenCreate(ModelMutation):
    auth_token = graphene.types.String(
        description="The newly created authentication token."
    )

    class Arguments:
        input = ServiceAccountTokenInput(
            required=True, description="Fields required to create a new auth token."
        )

    class Meta:
        return_field_name = "serviceAccountToken"
        description = "Creates a new token."
        model = models.AppToken
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def get_type_for_model(cls):
        return ServiceAccountToken

    @classmethod
    def perform_mutation(cls, root, info, **data):
        input_data = data.get("input", {})
        instance = cls.get_instance(info, **data)
        cleaned_input = cls.clean_input(info, instance, input_data)
        cleaned_input["app"] = cleaned_input.pop("service_account", None)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)
        response = cls.success_response(instance)
        response.auth_token = instance.auth_token
        return response


class ServiceAccountTokenDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of an auth token to delete.", required=True)

    class Meta:
        return_field_name = "serviceAccountToken"
        description = "Deletes an authentication token assigned to service account."
        model = models.AppToken
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def get_type_for_model(cls):
        return ServiceAccountToken


class ServiceAccountCreate(ModelMutation):
    auth_token = graphene.types.String(
        description="The newly created authentication token."
    )

    class Arguments:
        input = ServiceAccountInput(
            required=True,
            description="Fields required to create a new service account.",
        )

    class Meta:
        return_field_name = "serviceAccount"
        description = "Creates a new service account."
        model = models.App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def get_type_for_model(cls):
        return ServiceAccount

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        cleaned_input = super().clean_input(info, instance, data, input_cls)
        # clean and prepare permissions
        if "permissions" in cleaned_input:
            permissions = cleaned_input.pop("permissions")
            cleaned_input["permissions"] = get_permissions(permissions)
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        instance.tokens.create(name="Default")

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.auth_token = instance.tokens.get().auth_token
        return response


class ServiceAccountUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            description="ID of a service account to update.", required=True
        )
        input = ServiceAccountInput(
            required=True,
            description="Fields required to update an existing service account.",
        )

    class Meta:
        return_field_name = "serviceAccount"
        description = "Updates an existing service account."
        model = models.App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        cleaned_input = super().clean_input(info, instance, data, input_cls)
        # clean and prepare permissions
        if "permissions" in cleaned_input:
            cleaned_input["permissions"] = get_permissions(cleaned_input["permissions"])
        return cleaned_input

    @classmethod
    def get_type_for_model(cls):
        return ServiceAccount


class ServiceAccountDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            description="ID of a service account to delete.", required=True
        )

    class Meta:
        return_field_name = "serviceAccount"
        description = "Deletes a service account."
        model = models.App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def get_type_for_model(cls):
        return ServiceAccount


class ServiceAccountUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        return_field_name = "serviceAccount"
        description = "Updates private metadata for a service account."
        permissions = (AppPermission.MANAGE_APPS,)
        model = models.App
        public = False
        error_type_class = AccountError
        error_type_field = "account_errors"


class ServiceAccountClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        return_field_name = "serviceAccount"
        description = "Clear private metadata for a service account."
        model = models.App
        permissions = (AppPermission.MANAGE_APPS,)
        public = False
        error_type_class = AccountError
        error_type_field = "account_errors"
