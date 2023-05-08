from ...pharmacy import models


def resolve_patient_by_uuid(customer_uuid):
    return models.Patient.objects.filter(customer__uuid=customer_uuid).first()
