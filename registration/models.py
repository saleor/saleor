import os

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ExternalUserData(models.Model):
    user = models.ForeignKey(
        User, related_name='external_ids', null=True, blank=True)
    provider = models.TextField(db_index=True)
    username = models.TextField(db_index=True)

    class Meta:
        unique_together = (('provider', 'username'),)


class EmailConfirmation(models.Model):
    email = models.EmailField()
    external_user = models.ForeignKey(ExternalUserData, null=True, blank=True)
    token = models.CharField(
        max_length=32, default=lambda: os.urandom(16).encode('hex'))

    def get_confirmed_user(self):
        """Confirm that user owns this email address and return User insatnce.
        """
        if self.external_user and self.external_user.user:
            return self.external_user.user

        user, _created = User.objects.get_or_create(email=self.email)

        if self.external_user:
            self.external_user.user = user
            self.external_user.save()

        return user
