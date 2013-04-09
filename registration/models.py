import os
from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()
now = datetime.now


class ExternalUserData(models.Model):

    user = models.ForeignKey(
        User, related_name='external_ids', null=True, blank=True)
    provider = models.TextField(db_index=True)
    username = models.TextField(db_index=True)

    class Meta:
        unique_together = [['provider', 'username']]


class EmailConfirmation(models.Model):

    email = models.EmailField()
    external_user = models.ForeignKey(
        ExternalUserData, null=True, blank=True,
        related_name='email_confirmations')
    token = models.CharField(
        max_length=32, default=lambda: os.urandom(16).encode('hex'))
    valid_until = models.DateTimeField(
        default=lambda: now() + timedelta(settings.ACCOUNT_ACTIVATION_DAYS))

    def get_or_create_user(self):
        """Confirm that user owns this email address and return User insatnce.
        """
        if self.external_user and self.external_user.user:
            return self.external_user.user

        user, _created = User.objects.get_or_create(
            email=self.email, defaults={'is_active': True})

        if self.external_user:
            self.external_user.user = user
            self.external_user.save()

        return user
