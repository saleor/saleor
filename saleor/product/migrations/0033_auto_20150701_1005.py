# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.utils.text import slugify


def generate_name(apps, schema_editor):
    ProductAttribute = apps.get_model("product", "ProductAttribute")
    for attr in ProductAttribute.objects.all():
        attr.name = slugify(attr.display)
        attr.save()


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0032_auto_20150701_1004'),
    ]

    operations = [
        migrations.RunPython(generate_name),
    ]

