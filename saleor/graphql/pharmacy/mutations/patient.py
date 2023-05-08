import graphene

from ..enums import GenderEnum
from ...core.mutations import BaseMutation
from ....pharmacy import models
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ..types import PatientError, PatientType
from ....pharmacy.error_codes import PatientErrorCode
from ...account.types import User
from ....account.models import User as UserModel


class PatientInput(graphene.InputObjectType):
    customer = graphene.ID(description="Customer ID", required=True, name="customer")
    date_of_birth = graphene.DateTime(description="Date of Birth", required=True)
    gender_assigned_at_birth = GenderEnum(
        description="Gender assigned at birth.", required=True
    )


class PatientCreate(BaseMutation):
    patient = graphene.Field(PatientType)

    class Arguments:
        input = PatientInput(
            description="Fields required to create a Patient", required=True
        )

    class Meta:
        description = "Creates a new Patient."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = PatientError
        error_type_field = "patient_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, input):
        # These global ID fields from relay use id right now which is bad.  We should
        # be using UUID values.

        _, customer_id = graphene.Node.from_global_id(input["customer"])
        customer = UserModel.objects.get(uuid=customer_id)
        try:
            patient = models.Patient.objects.get(customer=customer)
        except models.Patient.DoesNotExist:
            patient = None

        if patient:
            return cls(
                errors=[
                    PatientError(
                        field="customer",
                        message="Customer already has a patient profile.  Use patientUpdate mutation to update the patient profile.",
                        code=PatientErrorCode.ALREADY_EXISTS,
                    )
                ]
            )
        else:
            patient = models.Patient.objects.create(
                customer=customer,
                date_of_birth=input["date_of_birth"],
                gender_assigned_at_birth=input["gender_assigned_at_birth"],
            )
            return cls(patient=patient)


class PatientUpdate(BaseMutation):
    patient = graphene.Field(PatientType)

    class Arguments:
        input = PatientInput(
            description="Fields required to update a Patient", required=True
        )

    class Meta:
        description = "Updates a Patient."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = PatientError
        error_type_field = "patient_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, input):
        # These global ID fields from relay use id right now which is bad.  We should
        # be using UUID values.

        _, customer_id = graphene.Node.from_global_id(input["customer"])
        customer = UserModel.objects.get(uuid=customer_id)
        try:
            patient = models.Patient.objects.get(customer=customer)
        except models.Patient.DoesNotExist:
            patient = None

        if patient:
            patient.date_of_birth = input["date_of_birth"]
            patient.gender_assigned_at_birth = input["gender_assigned_at_birth"]
            patient.save(update_fields=["date_of_birth", "gender_assigned_at_birth"])
            return cls(patient=patient)
        else:
            return cls(
                errors=[
                    PatientError(
                        field="customer",
                        message="Patient does not exist.  Use patientCreate mutation to create a new patient profile.",
                        code=PatientErrorCode.NOT_FOUND,
                    )
                ]
            )
