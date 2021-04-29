from django.db import models

class Social(models.Model):
    action = models.BooleanField(default=True)

    class Meta:
        app_label = "social"
        ordering = ("pk",)
