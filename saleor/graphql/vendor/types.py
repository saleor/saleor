import graphene
from ...vendor import models
from ..core.types import ModelObjectType


class Vendor(ModelObjectType[models.Vendor]):
    id = graphene.GlobalID(required=True, description="The ID of the menu.")
    name = graphene.String(required=True, description="The name of the menu.")
    # slug = graphene.String(required=True, description="Slug of the menu.")

    class Meta:
        model = models.Vendor
        # fields = "__all__"
