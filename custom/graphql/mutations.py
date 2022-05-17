import graphene
from saleor.graphql.core.mutations import ModelMutation, ModelDeleteMutation
from custom import models
from .CustomError import CustomError
from .types import Custom


class CustomInput(graphene.InputObjectType):
    name = graphene.String(description="Custom name.")
    attribute = graphene.String(description="Custom name.")
    description = graphene.String(description="Custom name.")


class CustomCreate(ModelMutation):
    class Arguments:
        input = CustomInput(required=True,
                            description="Fields required to create custom.")

    class Meta:
        description = "Creates new custom."
        model = models.Custom
        error_type_class = CustomError
        error_type_field = "custom_errors"

    @classmethod
    def get_type_for_model(cls):
        return Custom

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        custom = super().perform_mutation(_root, info, **data)
        info.context.plugins.write_to_db(
            custom=custom
        )
        return custom


class CustomUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of a custom update.", required=True)
        input = CustomInput(required=True,
                            description="Fields required to create custom.")

    class Meta:
        description = "Creates new custom."
        model = models.Custom
        error_type_class = CustomError
        error_type_field = "custom_errors"


class CustomDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of a custom to delete.", required=True)

    class Meta:
        model = models.Custom
        description = "Deletes selected warehouse."
        error_type_class = CustomError
        error_type_field = "custom_errors"
