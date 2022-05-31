import graphene
from saleor.graphql.core.mutations import ModelMutation, ModelDeleteMutation, \
    BaseMutation
from custom import models
from .CustomError import CustomError
from .types import Custom as CustomType
from graphene_django import DjangoObjectType


class CustomInput(graphene.InputObjectType):
    name = graphene.String(description="Custom name.")
    attribute = graphene.String(description="Custom name.")
    description = graphene.String(description="Custom name.")
    pick_date = graphene.String(description="Custom name.")
    new_feature = graphene.String(description="Custom name.")


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
        return CustomType

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


class CustomCloneType(DjangoObjectType):
    class Meta:
        model = models.Custom
        fields = "__all__"


class CustomCloneInput(graphene.InputObjectType):
    id = graphene.ID(description="ID of a custom update.", required=True)


class CustomClone(graphene.Mutation):
    class Arguments:
        input = CustomCloneInput(required=True, description="")

    custom = graphene.Field(CustomCloneType)

    @classmethod
    def mutate(cls, root, info, input=None):
        print(input)
        old_custom = models.Custom.objects.filter(id=input['id']).first()
        new_custom = models.Custom(
            name=old_custom.name,
            attribute=old_custom.attribute,
            description=old_custom.description,
            metadata=old_custom.metadata,
            private_metadata=old_custom.private_metadata,
        )
        new_custom.save()
        return CustomClone(custom=new_custom)
