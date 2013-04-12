import os
from datetime import timedelta

from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string


User = get_user_model()
now = timezone.now
TOKEN_LENGTH = 32


class ExternalUserData(models.Model):

    user = models.ForeignKey(User, related_name='external_ids')
    service = models.TextField(db_index=True)
    username = models.TextField(db_index=True)

    class Meta:
        unique_together = [['service', 'username']]


class UniqueTokenManager(models.Manager):

    TOKEN_FIELD = 'token'

    def create(self, **kwargs):
        assert self.TOKEN_FIELD not in kwargs
        for x in xrange(100):
            token = get_random_string(TOKEN_LENGTH)
            conflict = EmailConfirmationRequest.objects.filter(token=token)
            if not conflict.exists():
                kwargs[self.TOKEN_FIELD] = token
                return super(UniqueTokenManager, self).create(**kwargs)
        raise RuntimeError('Could not create unique token.')


class EmailConfirmationRequest(models.Model):

    email = models.EmailField()
    token = models.CharField(max_length=TOKEN_LENGTH, unique=True)
    valid_until = models.DateTimeField(
        default=lambda: now() + timedelta(settings.ACCOUNT_ACTIVATION_DAYS))

    objects = UniqueTokenManager()

    def get_or_create_user(self):
        user, _created = User.objects.get_or_create(email=self.email)
        return user
