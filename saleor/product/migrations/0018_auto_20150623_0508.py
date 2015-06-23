# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0017_productvariant_attributes'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AttributeValue',
            new_name='AttributeChoiceValue',
        ),
        migrations.AlterField(
            model_name='product',
            name='attributes',
            field=models.ManyToManyField(related_name='products', null=True, to='product.ProductAttribute', blank=True),
        ),
    ]
