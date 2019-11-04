# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("account", "0001_initial")]

    replaces = [("userprofile", "0002_auto_20150907_0602")]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="addresses",
            field=models.ManyToManyField(to="account.Address", blank=True),
        )
    ]
