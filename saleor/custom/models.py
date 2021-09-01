from django.db import models


# Create your models here.
class CategoryCustom(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    is_deleted = models.BooleanField(default=0)

    class Meta:
        app_label = "custom"
        ordering = ("slug",)

    def __str__(self):
        return self.slug
