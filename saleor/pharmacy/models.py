from django.db import models
from django.conf import settings
from uuid import uuid4

from . import Gender


class PatientManager(models.Manager):
    def for_customer_uuid(self, customer_uuid):
        try:
            return self.get(customer__uuid=customer_uuid)
        except self.model.DoesNotExist:
            return None


class Patient(models.Model):
    # this is a substitute for HealthProfile...adding in gender_assigned_at_birth
    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="+",
        on_delete=models.CASCADE,
    )
    # customer_uuid can be found from customer.uuid
    # first_name can be found from customer.first_name
    # last_name can be found from customer.last_name
    date_of_birth = models.DateField(
        db_index=True, auto_now_add=False, null=False, blank=False
    )
    gender_assigned_at_birth = models.CharField(max_length=1, choices=Gender.CHOICES)

    objects = PatientManager()


class PatientInsurance(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        on_delete=models.CASCADE,
    )
    effective_date = models.DateField(
        db_index=True, auto_now_add=False, null=False, blank=False
    )
    termination_date = models.DateField(
        db_index=True, auto_now_add=False, null=True, blank=True
    )
    cardholder_id = models.CharField(max_length=25, null=False, blank=False)
    rx_bin = models.CharField(max_length=25, null=False, blank=False)
    rx_group = models.CharField(max_length=25, null=False, blank=False)
    pcn = models.CharField(max_length=25, null=True, blank=True)
    payer_name = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=25, null=True, blank=True)
    uuid = models.UUIDField(default=uuid4, unique=True)

    class Meta:
        ordering = ("effective_date",)


class PatientPrescription(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        on_delete=models.CASCADE,
    )
    uuid = models.UUIDField(default=uuid4, unique=True)
    prescription_number = models.CharField(max_length=25, null=False, blank=False)

    class Meta:
        ordering = ("-prescription_number",)
