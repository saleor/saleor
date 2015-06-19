# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_auto_20150616_0327'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bag',
            name='color',
        ),
        migrations.RemoveField(
            model_name='bag',
            name='product_ptr',
        ),
        migrations.RemoveField(
            model_name='bagvariant',
            name='product',
        ),
        migrations.RemoveField(
            model_name='shirt',
            name='color',
        ),
        migrations.RemoveField(
            model_name='shirt',
            name='product_ptr',
        ),
        migrations.RemoveField(
            model_name='shirtvariant',
            name='product',
        ),
        migrations.DeleteModel(
            name='Bag',
        ),
        migrations.DeleteModel(
            name='BagVariant',
        ),
        migrations.DeleteModel(
            name='Color',
        ),
        migrations.DeleteModel(
            name='Shirt',
        ),
        migrations.DeleteModel(
            name='ShirtVariant',
        ),
    ]
