from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("order", "0001_initial")]

    operations = [
        migrations.AlterModelOptions(name="payment", options={"ordering": ("-pk",)})
    ]
