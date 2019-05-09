# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from ..fields import JSONField


class Migration(migrations.Migration):
    replaces = [
        ('default', '0004_auto_20160423_0400'),
        ('social_auth', '0004_auto_20160423_0400')
    ]

    dependencies = [
        ('social_django', '0003_alter_email_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersocialauth',
            name='extra_data',
            field=JSONField(default=dict),
        )
    ]
