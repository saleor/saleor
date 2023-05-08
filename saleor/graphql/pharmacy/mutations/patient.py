import graphene

from .enums import GenderEnum
from ..i18n import I18nMixin
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation

class PatientInput(graphene.InputObjectType):
    date_of_birth = graphene.DateTime(description="Date of Birth", required=True)
    gender_assigned_at_birth = GenderEnum(
        description="Gender assigned at birth.", required=True
    )


class PatientCreate(ModelMutation, I18nMixin)
