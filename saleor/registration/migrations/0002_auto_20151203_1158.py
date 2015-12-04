# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externaluserdata',
            name='service',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='externaluserdata',
            name='username',
            field=models.CharField(max_length=255, db_index=True),
        ),
    ]
