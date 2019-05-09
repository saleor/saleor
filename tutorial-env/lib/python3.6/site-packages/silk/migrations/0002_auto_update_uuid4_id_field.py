# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('silk', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request',
            name='id',
            field=models.CharField(default=uuid.uuid4, max_length=36, serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='response',
            name='id',
            field=models.CharField(default=uuid.uuid4, max_length=36, serialize=False, primary_key=True),
        ),
    ]
