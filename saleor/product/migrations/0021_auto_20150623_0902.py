# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0020_auto_20150623_0800'),
    ]

    operations = [
        migrations.AddField(
            model_name='attributechoicevalue',
            name='color',
            field=models.CharField(blank=True, max_length=6, validators=[django.core.validators.RegexValidator('^([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')]),
        ),
        migrations.AddField(
            model_name='attributechoicevalue',
            name='image',
            field=versatileimagefield.fields.VersatileImageField(null=True, upload_to='attributes', blank=True),
        ),
    ]
