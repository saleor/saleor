import graphene
from graphene import relay

from .enums import GenderEnum
from ..core.types import ModelObjectType
from ...pharmacy import models
from ...pharmacy import error_codes as pharmacy_error_codes
from ..core.types.common import Error, NonNullList


PatientErrorCode = graphene.Enum.from_enum(pharmacy_error_codes.PatientErrorCode)


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


class PatientError(Error):
    code = PatientErrorCode(description="The error code.", required=True)

    attributes = NonNullList(
        graphene.ID,
        description="List of attributes IDs which causes the error.",
        required=False,
    )
    values = NonNullList(
        graphene.ID,
        description="List of attribute values IDs which causes the error.",
        required=False,
    )
