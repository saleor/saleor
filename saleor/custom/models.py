from django.db import models


class Custom(models.Model):
    name = models.CharField(max_length=250)
    address = models.CharField(max_length=255)

    class Meta:
        app_label = "custom"
