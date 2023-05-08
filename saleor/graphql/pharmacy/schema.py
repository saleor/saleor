import graphene

from ...permission.enums import OrderPermissions
from ..core import ResolveInfo
from ..core.fields import PermissionsField
from .resolvers import (
    resolve_patient_by_uuid,
)

from .mutations.patient import PatientCreate, PatientUpdate
from .types import PatientType


class PatientQueries(graphene.ObjectType):
    patient = PermissionsField(
        PatientType,
        description="Look up a customer health profile by Customer UUID.",
        customer_uuid=graphene.Argument(
            graphene.ID, description="UUID of customer", required=True
        ),
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
    )

    @staticmethod
    def resolve_patient(_root, _info: ResolveInfo, *, customer_uuid=None, **kwargs):
        if customer_uuid:
            return resolve_patient_by_uuid(customer_uuid=customer_uuid)


class PatientMutations(graphene.ObjectType):
    patient_create = PatientCreate.Field()
    patient_update = PatientUpdate.Field()
