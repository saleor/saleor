from uuid import uuid4

from django.db import models


class SavedEmail(models.Model):
    uuid = models.UUIDField(default=uuid4)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
