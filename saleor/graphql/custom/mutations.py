import graphene

from ...custom import models
from ...graphql.core.mutations import ModelMutation, ModelDeleteMutation
from ...graphql.custom.types.customs import CustomInput


class CustomCreate(ModelMutation):
    class Arguments:
        input = CustomInput(required=True,
                            description="Fields required to create custom.")

    class Meta:
        model = models.Custom
        description = "Create new custom"


class CustomUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of custom to update", required=True)
        input = CustomInput(required=False,
                            description="Fields required to update custom.")

    class Meta:
        model = models.Custom
        description = "Update custom"


class CustomDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of custom to delete", required=True)

    class Meta:
        model = models.Custom
        description = "Delete custom"
