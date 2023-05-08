import graphene
from graphene import relay

from .enums import GenderEnum
from ..core.types import ModelObjectType
from ...pharmacy import models


class PatientType(ModelObjectType[models.Patient]):
    id = graphene.ID(required=True)
    date_of_birth = graphene.DateTime(required=True)
    gender_assigned_at_birth = GenderEnum(required=True)
    customer = graphene.Field("saleor.graphql.account.types.User", required=True)

    class Meta:
        description = "The customer extensions for a Patient object."
        interfaces = [relay.Node]
        model = models.Patient

    @staticmethod
    def resolve_date_of_birth(root: models.Patient, _info):
        return root.date_of_birth
