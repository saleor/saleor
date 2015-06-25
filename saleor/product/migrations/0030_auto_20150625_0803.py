# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.text import slugify


def generate_slug(apps, schema_editor):
    ProductAttribute = apps.get_model("product", "ProductAttribute")
    for attr in ProductAttribute.objects.all():
        attr.slug = slugify(attr.display)
        attr.save()


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0029_auto_20150625_0802'),
    ]

    operations = [
        migrations.RunPython(generate_slug),
    ]
