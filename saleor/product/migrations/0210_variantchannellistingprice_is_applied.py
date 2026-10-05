from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0209_variantchannellistingprice"),
    ]

    operations = [
        migrations.AddField(
            model_name="variantchannellistingprice",
            name="is_applied",
            field=models.BooleanField(default=False),
        ),
    ]
