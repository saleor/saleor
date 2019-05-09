# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("order", "0004_order_total")]

    operations = [
        migrations.AddField(
            model_name="deliverygroup",
            name="last_updated",
            field=models.DateTimeField(auto_now=True, null=True),
        )
    ]
