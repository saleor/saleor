from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ExternalUserID(models.Model):
    user = models.ForeignKey(User, related_name='external_ids')
    provider = models.TextField()
    username = models.TextField()

    class Meta:
        unique_together = (('provider', 'username'),)
