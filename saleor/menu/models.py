from django.db import models
from mptt.managers import TreeManager
from mptt.models import MPTTModel


class Menu(models.Model):
    slug = models.SlugField(max_length=50)


class MenuItem(MPTTModel):
    menu = models.ForeignKey(
        Menu, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    sort_order = models.PositiveIntegerField(editable=False)
    url = models.URLField(max_length=256)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        on_delete=models.CASCADE)

    objects = models.Manager()
    tree = TreeManager()

    class Meta:
        ordering = ('sort_order',)
        app_label = 'menu'

    def __str__(self):
        return self.name
