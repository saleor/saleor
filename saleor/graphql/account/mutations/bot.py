import graphene

from saleor.core.permissions import get_permissions

from ....account import models
from ...core.enums import PermissionEnum
from ...core.mutations import (
    ClearMetaBaseMutation,
    ModelDeleteMutation,
    ModelMutation,
    UpdateMetaBaseMutation,
)


class BotInput(graphene.InputObjectType):
    name = graphene.types.String(description="Name of the bot")
    is_active = graphene.types.Boolean(description="Determine if bot should be enabled")
    permissions = graphene.List(
        PermissionEnum,
        description="List of permission code names to assign to this bot.",
    )


class BotCreate(ModelMutation):
    auth_token = graphene.types.String(
        description="The newly created authentication token"
    )

    class Arguments:
        input = BotInput(
            required=True, description="Fields required to create a new bot."
        )

    class Meta:
        description = "Creates a new bot"
        model = models.Bot
        permissions = ("account.manage_bots",)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        # clean and prepare permissions
        if "permissions" in cleaned_input:
            permissions = cleaned_input.pop("permissions")
            cleaned_input["permissions"] = get_permissions(permissions)
        return cleaned_input

    @classmethod
    def perform_mutation(cls, root, info, **data):
        response = super().perform_mutation(root, info, **data)
        response.auth_token = response.bot.auth_token
        return response


class BotUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of a bot to update.", required=True)
        input = BotInput(
            required=True, description="Fields required to update an existing bot."
        )

    class Meta:
        description = "Updates an existing bot"
        model = models.Bot
        permissions = ("account.manage_bots",)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        # clean and prepare permissions
        if "permissions" in cleaned_input:
            permissions = cleaned_input.pop("permissions")
            cleaned_input["permissions"] = get_permissions(permissions)
        return cleaned_input


class BotDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of a bot to delete.", required=True)

    class Meta:
        description = "Deletes a bot"
        model = models.Bot
        permissions = ("account.manage_bots",)


class BotUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Updates private metadata for bot."
        permissions = ("account.manage_bots",)
        model = models.Bot
        public = False


class BotClearStoredPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clear stored metadata value."
        model = models.Bot
        permissions = ("account.manage_bots",)
        public = False
