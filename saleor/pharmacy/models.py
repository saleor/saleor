from django.db import models
from django.conf import settings
from uuid import uuid4

from . import Gender


class Patient(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        on_delete=models.CASCADE,
    )
    date_of_birth = models.DateField(
        db_index=True, auto_now_add=False, null=False, blank=False
    )
    gender_assigned_at_birth = models.CharField(max_length=1, choices=Gender.CHOICES)


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
