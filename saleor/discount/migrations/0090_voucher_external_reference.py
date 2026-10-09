from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0089_promotion_external_reference_unique_constraint"),
    ]

    operations = [
        migrations.AddField(
            model_name="voucher",
            name="external_reference",
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
