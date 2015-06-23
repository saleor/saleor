# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0016_auto_20150622_0808'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='attributes',
            field=jsonfield.fields.JSONField(verbose_name='attributes', blank=True),
        ),
    ]
