from django.db import models


class Custom(models.Model):
    title = models.CharField(max_length=250)
    author = models.CharField(max_length=255)
    yearPublished = models.DateField(blank=True)
    review = models.IntegerField()

    class Meta:
        app_label = "custom"
