from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("account", "0002_auto_20150907_0602")]

    replaces = [("userprofile", "0003_auto_20151104_1102")]

    operations = [
        migrations.AddField(
            model_name="address",
            name="city_area",
            field=models.CharField(max_length=128, verbose_name="district", blank=True),
        ),
        migrations.AlterField(
            model_name="address",
            name="postal_code",
            field=models.CharField(
                max_length=20, verbose_name="postal code", blank=True
            ),
        ),
    ]
