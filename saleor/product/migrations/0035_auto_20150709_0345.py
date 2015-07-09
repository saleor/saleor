# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import saleor.product.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0034_auto_20150706_0643'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='available_on',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='available on'),
        ),
        migrations.AlterField(
            model_name='product',
            name='weight',
            field=saleor.product.models.fields.WeightField(unit=b'lb', verbose_name='weight', max_digits=6, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='productvariant',
            name='weight_override',
            field=saleor.product.models.fields.WeightField(decimal_places=2, max_digits=6, blank=True, null=True, verbose_name='weight override', unit=b'lb'),
        ),
    ]
